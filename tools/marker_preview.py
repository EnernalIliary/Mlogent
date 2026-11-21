"""Capture one marker frame from the original headless game and render a PNG."""

import json
import shutil
from pathlib import Path


def capture(server, output, ticks):
    lines = server.js(_FRAME_JS)
    prefix = "MLOG_MARKER_FRAME "
    for line in lines:
        if line.startswith(prefix):
            shutil.copyfile(Path(server.workdir) / "marker-preview.png", output)
            return {"tick": ticks, **json.loads(line[len(prefix):])}
    raise RuntimeError("headless server did not return marker state")


_FRAME_JS = r"""
(function(){
    var Vars = Packages.mindustry.Vars, tilesize = Vars.tilesize;
    var registry = Vars.state.markers;
    /* The public iterator only contains world-visible markers and omits IDs. */
    var mapField = registry.getClass().getDeclaredField("map");
    mapField.setAccessible(true);
    var entries = mapField.get(registry).entries(), all = [];
    for(var index = 0; index < registry.size(); index++){
        var entry = entries.next();
        all.push({id: entry.key, value: entry.value});
    }
    all.sort(function(a, b){ return a.id - b.id; });
    var total = all.length, limit = 256;
    var layerField = Packages.java.lang.Class.forName(
        "mindustry.game.MapObjectives$ObjectiveMarker").getDeclaredField("drawLayer");
    layerField.setAccessible(true);
    function pos(p){ return [p.x / tilesize, p.y / tilesize]; }
    function color(c){ return "#" + String(c); }
    function packed(f){
        var bits = Packages.java.lang.Float.floatToRawIntBits(f), out = "#";
        for(var shift = 0; shift < 32; shift += 8){
            var channel = (bits >>> shift) & 255;
            if(shift === 24) channel = Math.round(channel * 255 / 254);
            out += ("0" + Math.min(255, channel).toString(16)).slice(-2);
        }
        return out;
    }
    var markers = all.slice(0, limit).map(function(entry){
        var m = entry.value;
        var type = String(m.getClass().getSimpleName()).replace(/Marker$/, "");
        type = type.charAt(0).toLowerCase() + type.slice(1);
        var out = {id: entry.id, type: type, world: m.world >= 0, minimap: m.minimap >= 0,
                   light: m.light >= 0, autoscale: m.autoscale, draw_layer: layerField.getFloat(m)};
        if(m.pos != null) out.pos = pos(m.pos);
        if(m.color != null) out.color = color(m.color);
        if(m.rotation != null) out.rotation = m.rotation;
        if(m.radius != null) out.radius = m.radius / (
            type === "point" || type === "light" ? 1 : tilesize);
        if(m.stroke != null) out.stroke = m.stroke / tilesize;
        if(m.text != null){
            var label = String(m.text);
            out.text = label.slice(0, 512);
            if(label.length > 512) out.text_truncated = true;
            out.font_size = m.fontSize;
            out.label_flags = m.flags;
            out.text_align = m.textAlign;
            out.line_align = m.lineAlign;
        }
        if(type === "line"){
            out.end = pos(m.endPos);
            out.colors = [color(m.color1), color(m.color2)];
            out.outline = m.outline;
        }
        if(type === "shape"){
            out.sides = m.sides;
            out.fill = m.fill;
            out.outline = m.outline;
            out.arc = [m.startAngle, m.endAngle];
        }
        if(type === "shapeText"){
            out.sides = m.sides;
            out.text_height = m.textHeight / tilesize;
            out.outline = true;
        }
        if(type === "texture" || type === "quad") out.texture = String(m.texture.value).slice(0, 256);
        if(type === "texture") out.size = [m.width / tilesize, m.height / tilesize];
        if(type === "quad"){
            out.vertices = [];
            for(var i = 0; i < 24; i += 6){
                out.vertices.push({pos: [m.vertices[i] / tilesize, m.vertices[i+1] / tilesize],
                                   color: packed(m.vertices[i+2]), uv: [m.vertices[i+3], m.vertices[i+4]],
                                   mix_color: packed(m.vertices[i+5])});
            }
        }
        return out;
    });
    var w = Vars.world.width(), h = Vars.world.height();
    var scale = Math.min(16, 768 / Math.max(w, h));
    var width = Math.max(1, Math.round(w * scale)), height = Math.max(1, Math.round(h * scale));
    var awt = Packages.java.awt, geom = awt.geom;
    var rgb = awt.image.BufferedImage.TYPE_INT_RGB, hints = awt.RenderingHints;
    var canvas = new awt.image.BufferedImage(width * 2, height * 2, rgb);
    var g = canvas.createGraphics();
    g.scale(2, 2);
    var gray = new awt.Color(0xff313843 | 0, true);
    function x(v){ return (v + 0.5) * scale; }
    function y(v){ return height - (v + 0.5) * scale; }
    function paint(hex){
        var rgba = parseInt(hex.slice(1), 16) | 0;
        return new awt.Color((rgba >>> 8) | (rgba << 24), true);
    }
    function stroke(px){
        g.setStroke(new awt.BasicStroke(Math.max(0.5, Math.min(768, px))));
    }
    function poly(m, start, sweep, fill, radius){
        var path = new geom.Path2D.Double(), sides = Math.min(200, Math.max(3, m.sides));
        var segments = Math.max(1, Math.ceil(sides * sweep / 360));
        if(fill && sweep < 360) path.moveTo(x(m.pos[0]), y(m.pos[1]));
        for(var i = 0; i <= segments; i++){
            var angle = (m.rotation + start + sweep * i / segments) * Math.PI / 180;
            var xx = x(m.pos[0] + radius * Math.cos(angle));
            var yy = y(m.pos[1] + radius * Math.sin(angle));
            if(i || (fill && sweep < 360)) path.lineTo(xx, yy);
            else path.moveTo(xx, yy);
        }
        if(fill || sweep === 360) path.closePath();
        return path;
    }
    function drawText(m, offset){
        if(!m.font_size) return;
        var size = Math.round(Math.max(9, Math.min(144, 1.5 * scale * m.font_size)));
        g.setFont(new awt.Font("SansSerif", awt.Font.PLAIN, size));
        var fm = g.getFontMetrics(), rows = m.text.split(/\r?\n/), lineHeight = fm.getHeight();
        var blockWidth = 0, blockHeight = rows.length * lineHeight;
        rows.forEach(function(row){ blockWidth = Math.max(blockWidth, fm.stringWidth(row)); });
        /* Arc Align bits are top=2, bottom=4, left=8, right=16. */
        var left = x(m.pos[0]) - ((m.text_align & 8) ? 0 : (m.text_align & 16) ? blockWidth : blockWidth / 2);
        var top = y(m.pos[1] + offset) - ((m.text_align & 2) ? 0 : (m.text_align & 4) ? blockHeight : blockHeight / 2);
        if(m.label_flags & 1){
            g.setColor(new awt.Color(0xa0000000 | 0, true));
            g.fill(new geom.Rectangle2D.Double(left - 3, top, blockWidth + 6, blockHeight));
        }
        rows.forEach(function(row, i){
            var space = blockWidth - fm.stringWidth(row);
            var xx = Math.round(left + ((m.line_align & 8) ? 0 : (m.line_align & 16) ? space : space / 2));
            var yy = Math.round(top + i * lineHeight + fm.getAscent());
            if(m.label_flags & 2){
                g.setColor(awt.Color.black);
                g.drawString(row, xx + 1, yy + 1);
            }
            g.setColor(awt.Color.white);
            g.drawString(row, xx, yy);
        });
    }
    function draw(m){
        if(m.type === "quad"){
            var quad = new geom.Path2D.Double();
            m.vertices.forEach(function(v, i){
                if(i) quad.lineTo(x(v.pos[0]), y(v.pos[1]));
                else quad.moveTo(x(v.pos[0]), y(v.pos[1]));
            });
            quad.closePath();
            g.setColor(paint(m.vertices[0].color));
            /* Antialias after compositing so adjacent fill pieces share a clean edge. */
            g.setRenderingHint(hints.KEY_ANTIALIASING, hints.VALUE_ANTIALIAS_OFF);
            g.fill(quad);
            g.setRenderingHint(hints.KEY_ANTIALIASING, hints.VALUE_ANTIALIAS_ON);
        }else if(m.type === "line"){
            var x1 = x(m.pos[0]), y1 = y(m.pos[1]), x2 = x(m.end[0]), y2 = y(m.end[1]);
            var line = new geom.Line2D.Double(x1, y1, x2, y2);
            if(m.outline){
                stroke((m.stroke + 2 / tilesize) * scale);
                g.setColor(gray); g.draw(line);
            }
            stroke(m.stroke * scale);
            g.setPaint(new awt.GradientPaint(x1, y1, paint(m.colors[0]), x2, y2, paint(m.colors[1])));
            g.draw(line);
        }else if(m.type === "shape" || m.type === "shapeText"){
            var a = m.arc || [0, 360], start = Math.min(a[0], a[1]) % 360;
            var sweep = Math.min(360, Math.abs(a[1] - a[0])), sw = m.stroke || 1 / tilesize;
            var path = poly(m, start, sweep, m.fill, m.radius + (m.fill ? 0 : 1 / tilesize));
            if(!m.fill && m.outline){
                stroke((sw + 2 / tilesize) * scale);
                g.setColor(gray); g.draw(path);
            }
            g.setColor(paint(m.color));
            stroke(sw * scale);
            if(m.fill) g.fill(path);
            else g.draw(path);
            if(m.type === "shapeText") drawText(m, m.radius + m.text_height);
        }else if(m.type === "point"){
            var r = m.radius * scale;
            stroke(m.stroke * scale);
            g.setColor(paint(m.color));
            g.draw(new geom.Ellipse2D.Double(x(m.pos[0]) - r, y(m.pos[1]) - r, 2 * r, 2 * r));
        }else if(m.type === "text"){
            drawText(m, 0);
        }
    }
    function validGeometry(value){
        if(typeof value === "number") return isFinite(value);
        if(value && typeof value === "object"){
            return Object.keys(value).every(function(key){ return validGeometry(value[key]); });
        }
        return true;
    }
    try {
        g.setColor(new awt.Color(0xff141922 | 0, true)); g.fillRect(0, 0, width, height);
        g.setColor(new awt.Color(0xff232b37 | 0, true));
        var grid = Math.max(1, Math.ceil(12 / scale));
        for(var dx = 0; dx <= w; dx += grid){
            var px = Math.round(dx * scale); g.drawLine(px, 0, px, height);
        }
        for(var dy = 0; dy <= h; dy += grid){
            var py = height - Math.round(dy * scale); g.drawLine(0, py, width, py);
        }
        g.setRenderingHint(hints.KEY_ANTIALIASING, hints.VALUE_ANTIALIAS_ON);
        var drawOrder = markers.slice().sort(function(a, b){ return a.draw_layer - b.draw_layer || a.id - b.id; });
        var supported = ["text", "line", "shape", "shapeText", "point", "quad"];
        drawOrder.forEach(function(m){
            if(!m.world) m.preview = "hidden";
            else if(supported.indexOf(m.type) < 0 ||
                   (m.type === "quad" && m.texture !== "white")) m.preview = "unsupported";
            else if(!validGeometry(m)) m.preview = "invalid_geometry";
            else {
                draw(m);
                m.preview = "drawn";
            }
        });
    } finally {
        g.dispose();
    }
    var image = new awt.image.BufferedImage(width, height, rgb), output = image.createGraphics();
    try{
        output.setRenderingHint(hints.KEY_INTERPOLATION, hints.VALUE_INTERPOLATION_BILINEAR);
        output.drawImage(canvas, 0, 0, width, height, null);
    }finally{
        output.dispose();
    }
    if(!Packages.javax.imageio.ImageIO.write(image, "png", new Packages.java.io.File("marker-preview.png"))){
        throw new Error("PNG encoder unavailable");
    }
    print("MLOG_MARKER_FRAME " + JSON.stringify({
        bounds: {min_x: -0.5, min_y: -0.5, max_x: w - 0.5, max_y: h - 0.5, units: "tiles"},
        image: {width: width, height: height, background: "tile_grid"},
        total: total, truncated: total > limit, markers: markers
    }));
})()
"""
