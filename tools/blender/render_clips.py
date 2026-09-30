"""Blender (bpy) pre-render of the All for One University opening clips.
usage: python3 op.py <clip> <orient: w|p> <mode: still|anim> [frame]
clips: towers, desk, friends, star, kmitl
"""
import bpy, math, sys, os, random
from mathutils import Vector, Euler

CLIP, ORIENT, MODE = sys.argv[-3], sys.argv[-2], sys.argv[-1] if not sys.argv[-1].isdigit() else sys.argv[-2]
if sys.argv[-1].isdigit():
    CLIP, ORIENT, MODE, FR = sys.argv[-4], sys.argv[-3], sys.argv[-2], int(sys.argv[-1])
else:
    FR = None
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out', f'{CLIP}-{ORIENT}' + ('-idle' if MODE == 'idle' else ''))
os.makedirs(OUT, exist_ok=True)
FPS, SECONDS = 12, 4
rnd = random.Random(7)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = 'CYCLES'
sc.cycles.device = 'CPU'
sc.cycles.samples = 8
sc.cycles.use_denoising = True
sc.cycles.max_bounces = 3; sc.cycles.diffuse_bounces = 2; sc.cycles.glossy_bounces = 2; sc.cycles.transmission_bounces = 2
sc.cycles.use_adaptive_sampling = True
sc.render.fps = FPS
sc.frame_start, sc.frame_end = 1, FPS * SECONDS
W, H = (960, 540) if ORIENT == 'w' else (540, 960)
RS = float(os.environ.get('RES', '1')); W, H = int(W * RS), int(H * RS)
LAYER = os.environ.get('LAYER', '')
sc.render.resolution_x, sc.render.resolution_y = W, H
sc.render.film_transparent = False
sc.view_settings.view_transform = 'Standard'
sc.view_settings.look = 'None'
sc.render.image_settings.file_format = 'PNG'
sc.render.image_settings.color_mode = 'RGBA'
# anime ink lines
sc.render.use_freestyle = True
sc.render.line_thickness_mode = 'ABSOLUTE'
sc.render.line_thickness = 1.1
vl = sc.view_layers[0]
vl.use_freestyle = True
ls = vl.freestyle_settings.linesets[0] if vl.freestyle_settings.linesets else vl.freestyle_settings.linesets.new('ink')
if ls.linestyle is None: ls.linestyle = bpy.data.linestyles.new('ink')
ls.linestyle.color = (0.08, 0.07, 0.2)
ls.select_by_visibility = True
ls.select_silhouette = True; ls.select_border = True; ls.select_crease = True
vl.freestyle_settings.crease_angle = math.radians(140)

# ---------------------------------------------------------------- helpers
def mat(name, color, rough=.6, metal=0., emit=None, estr=0., alpha=1.):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*color, 1)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    if emit:
        b.inputs['Emission Color'].default_value = (*emit, 1); b.inputs['Emission Strength'].default_value = estr
    if alpha < 1: b.inputs['Alpha'].default_value = alpha
    return m

def hexc(h):
    h = h.lstrip('#'); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple((x / 12.92) if x <= .04045 else ((x + .055) / 1.055) ** 2.4 for x in c)

def box(size, loc, m, rot=(0, 0, 0), name='box', bevel=0):
    bpy.ops.mesh.primitive_cube_add(location=loc, rotation=rot)
    o = bpy.context.object; o.name = name; o.scale = (size[0] / 2, size[1] / 2, size[2] / 2)
    bpy.ops.object.transform_apply(scale=True)
    if bevel:
        md = o.modifiers.new('bev', 'BEVEL'); md.width = bevel; md.segments = 2
    o.data.materials.append(m); return o

def sphere(r, loc, m, name='sph', seg=16):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=loc, segments=seg, ring_count=seg // 2)
    o = bpy.context.object; o.name = name; o.data.materials.append(m)
    bpy.ops.object.shade_smooth(); return o

def cyl(r, h, loc, m, rot=(0, 0, 0), v=16):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=h, location=loc, rotation=rot, vertices=v)
    o = bpy.context.object; o.data.materials.append(m); return o

def sky(kind='MULTIPLE_SCATTERING', elev=35, rot=150, strength=1.0, extra=None):
    w = bpy.data.worlds.new('world'); sc.world = w; w.use_nodes = True
    nt = w.node_tree; bg = nt.nodes['Background']
    s = nt.nodes.new('ShaderNodeTexSky'); s.sky_type = kind
    s.sun_elevation = math.radians(elev); s.sun_rotation = math.radians(rot)
    nt.links.new(s.outputs['Color'], bg.inputs['Color']); bg.inputs['Strength'].default_value = strength
    return s, bg

def flat_sky(top, bottom, strength=1.0):
    w = bpy.data.worlds.new('world'); sc.world = w; w.use_nodes = True
    nt = w.node_tree; bg = nt.nodes['Background']
    tc = nt.nodes.new('ShaderNodeTexCoord'); sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].position = .0; ramp.color_ramp.elements[0].color = (*bottom, 1)
    ramp.color_ramp.elements[1].position = .55; ramp.color_ramp.elements[1].color = (*top, 1)
    nt.links.new(tc.outputs['Generated'], sep.inputs[0]); nt.links.new(sep.outputs['Z'], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], bg.inputs['Color']); bg.inputs['Strength'].default_value = strength
    if os.environ.get('LAYER') in ('mid', 'front'):          # camera sees pure green (keyed out later), lighting stays normal
        lp = nt.nodes.new('ShaderNodeLightPath'); gb = nt.nodes.new('ShaderNodeBackground'); gb.inputs['Color'].default_value = (0, 1, 0, 1)
        mx = nt.nodes.new('ShaderNodeMixShader'); out = nt.nodes['World Output']
        nt.links.new(lp.outputs['Is Camera Ray'], mx.inputs[0]); nt.links.new(bg.outputs[0], mx.inputs[1]); nt.links.new(gb.outputs[0], mx.inputs[2])
        nt.links.new(mx.outputs[0], out.inputs['Surface'])
    return ramp, bg

def sun(elev, rot, energy=3.5, color=(1, .96, .9), angle=2):
    bpy.ops.object.light_add(type='SUN', rotation=(math.radians(90 - elev), 0, math.radians(rot)))
    l = bpy.context.object; l.data.energy = energy; l.data.color = color; l.data.angle = math.radians(angle)
    return l

def camera(loc, look, lens=28):
    bpy.ops.object.camera_add(location=loc); c = bpy.context.object; sc.camera = c
    c.data.lens = lens if ORIENT == 'w' else lens * (.78 if CLIP == 'kmitl' else 1.05)
    c.data.clip_end = 2000
    aim(c, look); return c

def aim(c, look):
    d = Vector(look) - c.location
    c.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()

def key_cam(c, frames):
    """frames: list of (frame, loc, look)"""
    for f, loc, look in frames:
        c.location = loc; aim(c, look)
        c.keyframe_insert('location', frame=f); c.keyframe_insert('rotation_euler', frame=f)
    for fc in c.animation_data.action.fcurves if hasattr(c.animation_data.action, 'fcurves') else []:
        for k in fc.keyframe_points: k.interpolation = 'SINE'; k.easing = 'EASE_IN_OUT'

CLOUDS = []
def cloud(loc, s, m):
    for dx, dy, dz, r in ((0, 0, 0, 1), (1.1, .2, -.15, .8), (-1.1, -.1, -.2, .75), (.5, .1, .45, .75), (-.5, 0, .35, .7)):
        CLOUDS.append(sphere(r * s, (loc[0] + dx * s, loc[1] + dy * s, loc[2] + dz * s), m, 'cloud', 20))

def tree(x, y, s, cols, trunk):
    cyl(.18 * s, 2 * s, (x, y, s), trunk, v=8)
    for dx, dy, dz, r in ((0, 0, 2.6, 1.3), (-.8, .2, 2.2, .95), (.85, -.1, 2.3, 1.0), (.1, .3, 3.3, .9)):
        sphere(r * s, (x + dx * s, y + dy * s, dz * s), rnd.choice(cols), 'leaf', 10)

def petals(center, size, count, frames, m):
    bpy.ops.mesh.primitive_plane_add(size=1, location=center); em = bpy.context.object
    em.scale = size; em.hide_render = True
    bpy.ops.mesh.primitive_ico_sphere_add(radius=.06, subdivisions=1, location=(0, 0, -50)); p = bpy.context.object
    p.scale = (1, .6, .15); p.data.materials.append(m)
    ps = em.modifiers.new('ps', 'PARTICLE_SYSTEM').particle_system.settings
    ps.count = count; ps.frame_start = -60; ps.frame_end = frames; ps.lifetime = 200
    ps.render_type = 'OBJECT'; ps.instance_object = p; ps.particle_size = 1; ps.size_random = .5
    ps.normal_factor = 0; ps.brownian_factor = .6; ps.effector_weights.gravity = .06
    ps.use_rotations = True; ps.rotation_mode = 'VEL'; ps.angular_velocity_mode = 'RAND'; ps.angular_velocity_factor = 4
    ps.object_align_factor = (.3, 0, -.2)
    return em

# ---------------------------------------------------------------- original anime-style characters
def toon(name, hexcol, shade=.38, rough=.7):
    """flat-ish cel look under Cycles: base colour + some self-emission so shadows stay colourful"""
    c = hexc(hexcol)
    return mat(name, c, rough, emit=c, estr=shade)

def skinobj(verts, edges, radii, m, name, sub=2):
    me = bpy.data.meshes.new(name); me.from_pydata(verts, edges, []); ob = bpy.data.objects.new(name, me)
    sc.collection.objects.link(ob)
    ob.modifiers.new('skin', 'SKIN')
    for i, r in enumerate(radii):
        rr = r if isinstance(r, tuple) else (r, r * .85)
        ob.data.skin_vertices[0].data[i].radius = rr
    ob.data.skin_vertices[0].data[0].use_root = True
    sd = ob.modifiers.new('sub', 'SUBSURF'); sd.levels = sub; sd.render_levels = sub
    me.materials.append(m)
    bpy.context.view_layer.objects.active = ob
    return ob

MATS = {}
def M(hexcol, shade=.38):
    k = (hexcol, shade)
    if k not in MATS: MATS[k] = toon('t' + hexcol + str(shade), hexcol, shade)
    return MATS[k]

def human(x, y, h=1.0, rotz=0.0, skin='#f2c7a5', top='#ffffff', bottom='#23305e', hair='#222a44', hair_style='spiky',
          arms=('down', 'down'), legs='stand', tie=None, face=True, stripe=None, big=1.0):
    """Builds one character facing -Y. Returns the root empty. Units: metres-ish, h scales everything."""
    if os.environ.get('NOCAST'):
        bpy.ops.object.empty_add(location=(x, y, 0)); return bpy.context.object
    bpy.ops.object.empty_add(location=(x, y, 0), rotation=(0, 0, rotz)); root = bpy.context.object
    kids = []
    def P(dx, dz, dy=0.0): return (dx * h, dy * h, dz * h)
    wide = big                     # shoulder / chest bulk
    # ---- legs + hips (bottom colour)
    if legs == 'stand':
        LV = [P(0, .92), P(-.11, .87), P(-.12, .47), P(-.12, .06), P(-.12, .02, -.1), P(.11, .87), P(.12, .47), P(.12, .06), P(.12, .02, -.1)]
    else:                          # kneeling on one knee, leaning forward
        LV = [P(0, .62, .05), P(-.12, .58, .05), P(-.12, .2, -.35), P(-.12, .08, -.05), P(-.12, .02, -.15), P(.12, .58, .05), P(.14, .08, .15), P(.14, .06, .55), P(.14, .02, .6)]
    LE = [(0, 1), (1, 2), (2, 3), (3, 4), (0, 5), (5, 6), (6, 7), (7, 8)]
    LR = [.17 * wide, .12, .1, .075, .06, .12, .1, .075, .06]
    kids.append(skinobj(LV, LE, LR, M(bottom), 'legs'))
    base = LV[0][2] / h
    lean = .28 if legs == 'kneel' else 0.0
    def T(dx, dz, dy=0.0): return P(dx, base + dz, dy - lean * dz)
    # ---- torso + arms (top colour)
    TV = [T(0, 0), T(0, .25), T(0, .48), T(0, .6), T(-.21 * wide, .52), T(.21 * wide, .52)]
    TE = [(0, 1), (1, 2), (2, 3), (2, 4), (2, 5)]
    TR = [(.18 * wide, .13), (.17 * wide, .12), (.22 * wide, .15), .065, .09 * wide, .09 * wide]
    hands = []
    for side, pose in zip((-1, 1), arms):
        s0 = 4 if side < 0 else 5
        if pose == 'down':   pts = [T(side * .27 * wide, .26), T(side * .29 * wide, .02)]
        elif pose == 'hip':  pts = [T(side * .4 * wide, .32, .02), T(side * .22 * wide, .1, -.03)]
        elif pose == 'up':   pts = [T(side * .3, .82), T(side * .36, 1.1)]
        elif pose == 'peace':pts = [T(side * .3, .52, -.12), T(side * .12, .76, -.2)]
        elif pose == 'hug':  pts = [T(side * .45, .54, .02), T(side * .78, .55, .04)]
        elif pose == 'fist': pts = [T(side * .22, .5, -.26), T(side * .1, .52, -.6)]      # punch straight at camera
        elif pose == 'cross':pts = [T(side * .24, .36, -.14), T(-side * .14, .38, -.18)]
        else:                pts = [T(side * .27, .26), T(side * .29, .02)]
        i0 = len(TV); TV.extend(pts); TE.extend([(s0, i0), (i0, i0 + 1)]); TR.extend([.088 * wide, .074 * wide])
        hands.append((pts[-1], pose))
    torso = skinobj(TV, TE, TR, M(top), 'torso'); kids.append(torso)
    for (hp, pose) in hands:
        r = (.11 if pose == 'fist' else .065) * h
        hd = sphere(r, hp, M(skin), 'hand', 16); hd.scale = (1, 1.1, .9); kids.append(hd)
        if pose == 'fist':             # knuckles
            for k in range(4):
                kn = sphere(r * .34, (hp[0] + (k - 1.5) * r * .45, hp[1] - r * .75, hp[2] + r * .25), M(skin), 'kn', 10); kids.append(kn)
    if stripe:                          # sporty jacket stripe down the sleeves / chest
        kids.append(box((.06 * h, .01 * h, .45 * h), T(-.07, .3, -.2 * wide), M(stripe, .5)))
        kids.append(box((.06 * h, .01 * h, .45 * h), T(.07, .3, -.2 * wide), M(stripe, .5)))
    if tie:
        kids.append(box((.05 * h, .02 * h, .3 * h), T(0, .4, -.19 * wide), M(tie, .5)))
    # ---- neck + head
    kids.append(cyl(.05 * h, .12 * h, T(0, .66), M(skin)))
    hc = T(0, .83)
    head = sphere(.14 * h, hc, M(skin), 'head', 24); head.scale = (1, .95, 1.12); kids.append(head)
    if face:
        for sx in (-1, 1):
            e = sphere(.024 * h, (hc[0] + sx * .052 * h, hc[1] - .128 * h, hc[2] + .01 * h), M('#1a1433', .9), 'eye', 10); e.scale = (.8, .5, 1.35); kids.append(e)
            hl = sphere(.008 * h, (hc[0] + sx * .048 * h, hc[1] - .142 * h, hc[2] + .025 * h), M('#ffffff', 1.2), 'hl', 8); kids.append(hl)
        mo = sphere(.03 * h, (hc[0], hc[1] - .128 * h, hc[2] - .07 * h), M('#fff4ee', .8), 'mouth', 10); mo.scale = (1.6, .4, .55); kids.append(mo)
    # ---- hair
    hm = M(hair, .45)
    cap = sphere(.152 * h, (hc[0], hc[1] + .012 * h, hc[2] + .03 * h), hm, 'hair', 24); cap.scale = (1.05, 1.02, .98); kids.append(cap)
    if hair_style == 'spiky':
        for k in range(11):
            a = -1.3 + k * .26
            loc = (hc[0] + math.sin(a) * .12 * h, hc[1] + .03 * h, hc[2] + .08 * h + math.cos(a) * .08 * h)
            bpy.ops.mesh.primitive_cone_add(radius1=.05 * h, depth=.2 * h, location=loc, rotation=(-.35, a * 1.05, 0), vertices=8)
            o = bpy.context.object; o.data.materials.append(hm); kids.append(o)
        for k in range(4):                        # fringe spikes over the forehead
            bpy.ops.mesh.primitive_cone_add(radius1=.035 * h, depth=.13 * h, location=(hc[0] + (k - 1.5) * .06 * h, hc[1] - .12 * h, hc[2] + .08 * h), rotation=(2.6, (k - 1.5) * .25, 0), vertices=6)
            o = bpy.context.object; o.data.materials.append(hm); kids.append(o)
    elif hair_style == 'long':
        kids.append(skinobj([(hc[0], hc[1] + .1 * h, hc[2] + .05 * h), (hc[0], hc[1] + .14 * h, hc[2] - .25 * h), (hc[0], hc[1] + .12 * h, hc[2] - .6 * h)], [(0, 1), (1, 2)], [(.15 * h, .08 * h), (.16 * h, .07 * h), (.1 * h, .04 * h)], hm, 'long'))
        for sx in (-1, 1):
            b = sphere(.07 * h, (hc[0] + sx * .12 * h, hc[1] - .02 * h, hc[2] - .08 * h), hm, 'side', 12); b.scale = (.6, .8, 1.8); kids.append(b)
    elif hair_style == 'bob':
        for sx in (-1, 1):
            b = sphere(.09 * h, (hc[0] + sx * .12 * h, hc[1] + .01 * h, hc[2] - .03 * h), hm, 'side', 12); b.scale = (.7, 1, 1.3); kids.append(b)
    elif hair_style == 'wild':                   # big swept-back mane (mentor)
        for k in range(9):
            a = -1.1 + k * .275
            loc = (hc[0] + math.sin(a) * .13 * h, hc[1] + .06 * h, hc[2] + .1 * h + math.cos(a) * .06 * h)
            bpy.ops.mesh.primitive_cone_add(radius1=.07 * h, depth=.32 * h, location=loc, rotation=(-.95, a * 1.2, 0), vertices=8)
            o = bpy.context.object; o.data.materials.append(hm); kids.append(o)
    for o in kids:
        o.parent = root
    return root

def star_mascot(loc, s, emit=0.0):
    import bmesh
    me = bpy.data.meshes.new('mstar'); bm = bmesh.new(); pts = []
    for k in range(10):
        r = 1.0 if k % 2 == 0 else .5; a = math.pi / 2 + k * math.pi / 5
        pts.append(bm.verts.new((math.cos(a) * r, 0, math.sin(a) * r)))
    f = bm.faces.new(pts); ex = bmesh.ops.extrude_face_region(bm, geom=[f])
    bmesh.ops.translate(bm, vec=(0, .35, 0), verts=[v for v in ex['geom'] if isinstance(v, bmesh.types.BMVert)])
    bm.to_mesh(me); ob = bpy.data.objects.new('mstar', me); sc.collection.objects.link(ob)
    me.materials.append(mat('mst', hexc('#ffd23f'), .5, emit=hexc('#ffd23f'), estr=.45 + emit))
    bv = ob.modifiers.new('bev', 'BEVEL'); bv.width = .08; bv.segments = 3
    ob.location = loc; ob.scale = (s, s, s)
    for sx in (-1, 1):
        e = sphere(.09 * s, (loc[0] + sx * .2 * s, loc[1] - .02 * s, loc[2] + .05 * s), M('#1a1433', .9), 'se', 12); e.scale = (.8, .4, 1.2)
        ch = sphere(.07 * s, (loc[0] + sx * .36 * s, loc[1] - .02 * s, loc[2] - .12 * s), M('#ff8fa3', .9), 'ck', 10); ch.scale = (1.3, .3, .7)
    return ob

# ---------------------------------------------------------------- clips
F = FPS * SECONDS
if CLIP == 'towers':
    # twin glass towers from a low angle, sakura, drifting clouds; camera tilts down from the sky
    rmp, _ = flat_sky(hexc('#1a4fc4'), hexc('#bfe3ff'), 1.0)
    rmp.color_ramp.elements[0].position = .25; rmp.color_ramp.elements[1].position = 1.0
    e = rmp.color_ramp.elements.new(.7); e.color = (*hexc('#4f97ec'), 1)
    sun(40, 200, 2.6)
    glass = mat('glass', hexc('#2f6fb8'), rough=.06, metal=.7)
    frame = mat('frame', hexc('#eef4fb'), .5)
    spandrel = mat('spandrel', hexc('#9fb8d6'), .45, .2)
    core = mat('core', hexc('#1d3b66'), .8)
    litw = mat('litw', hexc('#cfe6ff'), .3, emit=hexc('#fff1c9'), estr=1.2)
    for side in (-1, 1):
        cx = side * 9.5
        box((13.2, 11.2, 77), (cx, 0, 38.5), core)                               # dark interior mass: no see-through
        for i in range(24):
            z = i * 3.2
            box((14, 12, 2.1), (cx, 0, z + 1.9), glass, name='floor')
            box((14.15, 12.15, .95), (cx, 0, z + .45), spandrel)
            box((14.3, 12.3, .18), (cx, 0, z + 2.99), frame)
            for k in range(3):
                if rnd.random() < .35:
                    box((rnd.uniform(1.5, 3.5), .05, 1.6), (cx + rnd.uniform(-5, 5), -6.02, z + 1.9), litw)
        for k in range(15):
            x = cx - 7 + k * 1.0
            box((.16, .35, 77), (x, -6.12, 38.5), frame)
        for k in range(13):
            yv = -6 + k * 1.0
            box((.35, .16, 77), (cx + side * 7.08, yv, 38.5), frame)
        box((14.8, 12.8, 1.4), (cx, 0, 77.6), frame)
        box((9, 7, 5), (cx, 1, 80.8), spandrel); box((9.4, 7.4, .5), (cx, 1, 83.5), frame)
        cyl(.12, 8, (cx + side * 2, 1, 86), frame)
    # sky bridge
    box((5.2, 6, 5), (0, 0, 40), glass); box((5.6, 6.4, .4), (0, 0, 42.7), frame); box((5.6, 6.4, .4), (0, 0, 37.3), frame)
    # podium with columns
    box((50, 20, 1.2), (0, -2, .6), frame)
    for k in range(18):
        cyl(.45, 7, (-24 + k * 2.8, -10.5, 4.2), frame, v=12)
    box((52, 3, 1.2), (0, -10.5, 8.2), frame)
    # ground + sakura
    ground = mat('ground', hexc('#8fcf6e'), .9); bpy.ops.mesh.primitive_plane_add(size=400, location=(0, 0, 0)); bpy.context.object.data.materials.append(ground); GROUND = bpy.context.object
    pinks = [mat('p1', hexc('#f7a8c4'), .7), mat('p2', hexc('#fbc2d6'), .7), mat('p3', hexc('#f590b5'), .7)]
    trunk = mat('trunk', hexc('#6b3f33'), .8)
    for x, y, s in ((-22, -22, 2.2), (-15, -30, 1.8), (21, -24, 2.3), (14, -31, 1.7), (-27, -12, 1.9), (27, -13, 2.0)):
        tree(x, y, s, pinks, trunk)
    cm = mat('cloud', (1, 1, 1), .9, emit=(1, 1, 1), estr=.45)
    for x, y, z, s in ((-60, 90, 70, 9), (40, 110, 95, 11), (80, 60, 55, 7), (-20, 140, 120, 12), (-90, 70, 40, 8), (-38, 25, 118, 7), (46, 35, 135, 8), (-70, 40, 160, 9), (60, 10, 105, 6), (-45, 5, 210, 14), (40, 20, 240, 16), (-5, -15, 280, 18), (75, 0, 200, 13), (-85, 25, 250, 15), (15, 40, 190, 11)):
        if not os.environ.get('NOCLOUD'): cloud((x, y, z), s, cm)
    if MODE == 'idle':
        for o in CLOUDS:
            x0 = o.location.x; o.location.x = x0 - 16; o.keyframe_insert('location', frame=1)
            o.location.x = x0 + 16; o.keyframe_insert('location', frame=F)
    if not os.environ.get('TALL'): petals((0, -30, 30), (30, 15, 1), 700, F, pinks[1])
    c = camera((0, -26, 2), (0, 0, 60), 15)
    key_cam(c, [(1, (0, -24, 2.0), (0, 0, 95)), (F, (0, -36, 2.6), (0, 0, 22))] if MODE != 'idle' else [(1, (0, -24, 2.0), (0, 0, 95)), (F, (0, -24, 2.0), (0, 0, 95))])

elif CLIP == 'desk':
    flat_sky(hexc('#0d1438'), hexc('#1b1f4a'), .6)
    bpy.ops.object.light_add(type='AREA', location=(0, -4, 4), rotation=(math.radians(-60), 0, 0)); fl = bpy.context.object; fl.data.energy = 120; fl.data.color = (.45, .55, 1); fl.data.size = 6
    wood = mat('wood', hexc('#7a4f38'), .55)
    box((6, 3, .12), (0, 0, 1), wood)
    for x in (-2.8, 2.8): box((.12, 2.8, 1), (x, 0, .5), wood)
    wall = mat('wall', hexc('#232a5e'), .9)
    # window with city
    city = mat('city', hexc('#141a44'), .9, emit=hexc('#ffd98a'), estr=0)
    win = mat('window', hexc('#1a2a6c'), .3, emit=hexc('#2b3c8a'), estr=.6)
    box((2.6, .05, 1.7), (-2.2, 1.68, 3.1), win)
    for i in range(12):
        h = rnd.uniform(.3, 1.0); box((.2, .04, h), (-3.4 + i * .21, 1.64, 2.25 + h / 2), mat(f'b{i}', hexc('#10163a'), .9))
        for j in range(int(h / .18)):
            if rnd.random() < .4: box((.05, .045, .07), (-3.4 + i * .21 + rnd.uniform(-.06, .06), 1.615, 2.35 + j * .18), mat('lw', (0, 0, 0), .9, emit=hexc('#ffd98a'), estr=3))
    moon = mat('moon', (1, 1, 1), .5, emit=hexc('#fff3c4'), estr=6); sphere(.22, (-1.4, 1.62, 3.6), moon)
    # laptop
    alu = mat('alu', hexc('#c7d0e2'), .35, .6)
    box((1.6, 1.1, .05), (0, -.2, 1.09), alu)
    lid = box((1.6, .05, 1.05), (0, .36, 1.62), alu); lid.rotation_euler = (math.radians(-12), 0, 0)
    # code screen as emissive image made with PIL
    from PIL import Image, ImageDraw
    img = Image.new('RGB', (512, 330), (15, 22, 64)); d = ImageDraw.Draw(img); y = 18
    for i in range(12):
        ind = rnd.choice([0, 0, 24, 48]); c1 = rnd.choice([(255, 121, 198), (255, 210, 63), (189, 147, 249), (255, 138, 61)]); c2 = rnd.choice([(139, 233, 253), (80, 250, 123), (248, 248, 242)])
        l1, l2 = rnd.randint(30, 90), rnd.randint(60, 220)
        d.rounded_rectangle((20 + ind, y, 20 + ind + l1, y + 10), 5, fill=c1); d.rounded_rectangle((32 + ind + l1, y, 32 + ind + l1 + l2, y + 10), 5, fill=c2); y += 25
    tp = os.path.join(OUT, 'code.png'); img.save(tp)
    sm = bpy.data.materials.new('screen'); sm.use_nodes = True; nt = sm.node_tree
    tex = nt.nodes.new('ShaderNodeTexImage'); tex.image = bpy.data.images.load(tp)
    em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Strength'].default_value = 2.2
    nt.links.new(tex.outputs['Color'], em.inputs['Color']); nt.links.new(em.outputs[0], nt.nodes['Material Output'].inputs['Surface'])
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, .33, 1.63), rotation=(math.radians(78), 0, 0)); scr = bpy.context.object
    scr.scale = (1.45, .92, 1); scr.data.materials.append(sm)
    # lamp
    orange = mat('orange', hexc('#ff7a1f'), .4)
    cyl(.25, .06, (2, .3, 1.09), orange); cyl(.03, 1.1, (2, .3, 1.6), orange, rot=(0, .3, 0)); cyl(.03, .8, (1.7, .3, 2.2), orange, rot=(0, -.9, 0))
    bpy.ops.mesh.primitive_cone_add(radius1=.3, radius2=.08, depth=.35, location=(1.3, .25, 2.35), rotation=(0, 2.4, 0)); bpy.context.object.data.materials.append(orange)
    bpy.ops.object.light_add(type='SPOT', location=(1.25, .2, 2.25), rotation=(0, math.radians(-38), 0)); sp = bpy.context.object
    sp.data.energy = 600; sp.data.color = (1, .82, .55); sp.data.spot_size = math.radians(80); sp.data.spot_blend = .6
    bpy.ops.object.light_add(type='AREA', location=(0, -.4, 1.9), rotation=(math.radians(-70), 0, 0)); ar = bpy.context.object
    ar.data.energy = 90; ar.data.color = (.5, .75, 1); ar.data.size = 1.4
    # mug, notes, clock
    blue = mat('blue', hexc('#2f6fe0'), .4); cyl(.16, .34, (-1.6, -.1, 1.27), blue)
    for x, z, col in ((1.1, 3.4, '#ffe066'), (1.8, 3.2, '#ff9fbf'), (1.4, 2.7, '#9be7c4'), (2.4, 2.9, '#8fd0ff')):
        box((.5, .02, .5), (x, 1.68, z), mat('n' + col, hexc(col), .8), rot=(0, rnd.uniform(-.15, .15), 0))
    paper = mat('paper', hexc('#fff8e6'), .8); box((.9, .6, .02), (.9, -.8, 1.07), paper, rot=(0, 0, -.2))
    # ---- the rest of the study room (wide shot): floor, side wall, shelf, curtains, rug, chair, plant, fairy lights
    floor = mat('floor', hexc('#6b4a3a'), .7); box((16, 16, .1), (0, -4, -.05), floor)
    for i in range(-7, 8): box((.02, 16, .005), (i * .9, -4, .005), mat('seam', hexc('#4f3428'), .8))
    box((16, .2, 9), (0, 1.8, 4.5), wall)
    lw = mat('lwall', hexc('#2b3170'), .9); box((.2, 14, 9), (-6.6, -5, 4.5), lw)
    box((.25, 14, .25), (-6.5, -5, .12), mat('skirt', hexc('#1b1f4a'), .6)); box((16, .25, .25), (0, 1.7, .12), mat('skirt2', hexc('#1b1f4a'), .6))
    cur = mat('curtain', hexc('#b784ff'), .9, emit=hexc('#b784ff'), estr=.15)
    for x in (-3.75, -.65):
        for k in range(3): cyl(.14, 2.6, (x + (k - 1) * .16, 1.55, 3.0), cur, v=10)
    box((3.4, .1, .08), (-2.2, 1.55, 4.35), mat('rod', hexc('#e9d2a0'), .4, .5))
    # bookshelf on the left
    shelfw = mat('shelf', hexc('#8a5a3c'), .6)
    box((1.8, .6, .1), (-5.4, 1.35, 3.6), shelfw); box((1.8, .6, .1), (-5.4, 1.35, 2.6), shelfw); box((1.8, .6, .1), (-5.4, 1.35, 1.6), shelfw)
    box((.1, .6, 3.2), (-6.3, 1.35, 2.0), shelfw); box((.1, .6, 3.2), (-4.5, 1.35, 2.0), shelfw); box((1.8, .6, .1), (-5.4, 1.35, .45), shelfw)
    bcols = ['#ff7a8a', '#ffd23f', '#5fd3a3', '#6fa8ff', '#c38bff', '#ff9f5a']
    for zb in (1.65, 2.65, 3.65):
        x = -6.15
        while x < -4.75:
            w = rnd.uniform(.09, .16); h = rnd.uniform(.45, .75)
            box((w, .45, h), (x + w / 2, 1.35, zb + h / 2), mat('bk' + str(round(x, 2)) + str(zb), hexc(rnd.choice(bcols)), .7)); x += w + .015
    # rug, chair, cushion, plant, poster, fairy lights
    rug = mat('rug', hexc('#5fd3a3'), .9); cyl(2.3, .04, (.4, -2.0, .03), rug, v=48)
    cyl(1.7, .045, (.4, -2.0, .035), mat('rug2', hexc('#8fe6c2'), .9), v=48)
    chm = mat('chair', hexc('#ff6a3d'), .5); blk = mat('blk', hexc('#1d2233'), .5)
    # office chair, pulled out at the right end of the desk and turned a little toward us
    bpy.ops.object.empty_add(location=(2.6, -1.85, 0), rotation=(0, 0, math.radians(-28))); chroot = bpy.context.object
    parts = []
    for k in range(5):
        an = k * 2 * math.pi / 5 + .3
        parts.append(cyl(.035, .46, (math.cos(an) * .23, math.sin(an) * .23, .09), blk, rot=(0, math.radians(90), an), v=8))
        parts.append(sphere(.055, (math.cos(an) * .44, math.sin(an) * .44, .055), blk, seg=10))
    parts.append(cyl(.09, .08, (0, 0, .13), blk, v=12)); parts.append(cyl(.045, .42, (0, 0, .36), mat('chrome', hexc('#c7d0e2'), .3, .8), v=10))
    parts.append(box((.66, .62, .13), (0, 0, .62), chm, bevel=.06))
    parts.append(box((.66, .6, .05), (0, 0, .7), mat('seatpad', hexc('#ff8a5c'), .6), bevel=.04))
    parts.append(box((.08, .1, .5), (0, -.31, .92), blk))
    bk = box((.62, .11, .62), (0, -.36, 1.28), chm, bevel=.06); bk.rotation_euler = (math.radians(-8), 0, 0); parts.append(bk)
    for sx in (-1, 1):
        parts.append(box((.05, .05, .22), (sx * .34, .02, .8), blk)); parts.append(box((.08, .34, .05), (sx * .34, .02, .92), blk, bevel=.02))
    for o_ in parts: o_.parent = chroot
    cush = mat('cush', hexc('#ffb13d'), .8); o = sphere(1.0, (-3.1, -1.4, .2), cush, seg=24); o.scale = (1.1, .9, .3)
    pot = mat('pot', hexc('#e8835a'), .6); cyl(.38, .7, (4.6, .6, .35), pot)
    leafm = [mat('pl1', hexc('#4fae5a'), .8), mat('pl2', hexc('#6cc36b'), .8)]
    for k in range(7): sp_ = sphere(rnd.uniform(.35, .5), (4.6 + rnd.uniform(-.4, .4), .6 + rnd.uniform(-.3, .3), 1.0 + rnd.uniform(0, .9)), leafm[k % 2], seg=12)
    box((1.4, .06, 1.9), (4.2, 1.68, 3.6), mat('frame', hexc('#fff2d9'), .6)); box((1.2, .04, 1.7), (4.2, 1.64, 3.6), mat('poster', hexc('#ff8fb8'), .7, emit=hexc('#ff8fb8'), estr=.25))
    bulb = mat('fairy', hexc('#ffd98a'), .3, emit=hexc('#ffc85a'), estr=5)
    for k in range(26):
        t = k / 25; x = -6.2 + t * 12.4; z = 5.2 - math.sin(t * math.pi * 3) ** 2 * .45
        sphere(.07, (x, 1.62, z), bulb, seg=8)
    box((12.4, .02, .02), (0, 1.63, 5.15), mat('wire', hexc('#1b1f4a'), .6))
    bpy.ops.object.light_add(type='POINT', location=(-2, -1, 4.6)); l = bpy.context.object; l.data.energy = 160; l.data.color = (1, .8, .55); l.data.shadow_soft_size = 1.5
    bpy.ops.object.light_add(type='AREA', location=(-2.5, -6, 3.5), rotation=(math.radians(70), 0, math.radians(-15))); l = bpy.context.object; l.data.energy = 260; l.data.color = (.55, .6, 1); l.data.size = 5
    # the hamster: a 2D card standing IN the 3D room (lit by the lamp, casting a shadow, no ink box around it)
    CAM_A, LOOK_A, CAM_B, LOOK_B = ((.6, -9.4, 2.6), (-.5, .3, 1.75), (.4, -8.2, 2.35), (-.4, .3, 1.7)) if ORIENT == 'w' else ((-1.1, -9.4, 2.6), (-1.65, .3, 2.25), (-1.0, -8.3, 2.45), (-1.55, .3, 2.2))
    hp = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'p-study.png')
    if not os.path.exists(hp):
        from PIL import Image as _I; _I.open('/home/claude/afo-repo/assets/img/cast/p-study.webp').save(hp)
    hm = bpy.data.materials.new('ham'); hm.use_nodes = True; nt = hm.node_tree; bs = nt.nodes['Principled BSDF']
    ht = nt.nodes.new('ShaderNodeTexImage'); ht.image = bpy.data.images.load(hp)
    nt.links.new(ht.outputs['Color'], bs.inputs['Base Color']); nt.links.new(ht.outputs['Alpha'], bs.inputs['Alpha'])
    nt.links.new(ht.outputs['Color'], bs.inputs['Emission Color']); bs.inputs['Emission Strength'].default_value = .55; bs.inputs['Roughness'].default_value = .8
    try: hm.surface_render_method = 'DITHERED'
    except Exception: pass
    hx, hy, hh = -3.05, -1.45, 1.9; hw = hh * 685 / 718
    rz = math.atan2(CAM_A[0] - hx, -(CAM_A[1] - hy))
    bpy.ops.mesh.primitive_plane_add(size=1, location=(hx, hy, .28 + hh / 2), rotation=(math.radians(90), 0, rz)); card = bpy.context.object
    card.scale = (hw, hh, 1); card.data.materials.append(hm)
    nofs = bpy.data.collections.new('nofs_d'); sc.collection.children.link(nofs)
    for col in card.users_collection: col.objects.unlink(card)
    nofs.objects.link(card)
    ls.select_by_collection = True; ls.collection = nofs; ls.collection_negation = 'EXCLUSIVE'
    c = camera(CAM_A, LOOK_A, 28)
    key_cam(c, [(1, CAM_A, LOOK_A), (F, CAM_B, LOOK_B)])

elif CLIP == 'friends':
    flat_sky(hexc('#3b2a8f'), hexc('#ff9a5c'), 1.0)
    sun(8, 0, 1.2, (1, .55, .4))
    sd = mat('sundisc', (1, 1, 1), .5, emit=hexc('#fff0c0'), estr=4); sphere(13, (5, 120, 15), sd)
    roof = mat('roof', hexc('#3a2a5a'), .8); bpy.ops.mesh.primitive_plane_add(size=60, location=(0, 0, 0)); bpy.context.object.data.materials.append(roof)
    rail = mat('rail', hexc('#1c1236'), .5)
    box((30, .12, .12), (0, 6, 1.1), rail)
    for k in range(16): box((.08, .08, 1.1), (-15 + k * 2, 6, .55), rail)
    city = mat('bld', hexc('#5a2f7a'), .9)
    for i in range(40):
        w, h = rnd.uniform(3, 7), rnd.uniform(6, 30)
        box((w, w, h), (rnd.uniform(-90, 90), rnd.uniform(40, 120), h / 2 - 6), city)
    body = mat('body', hexc('#1d1238'), .9)
    def skel(verts, edges, radii, m, name):
        me = bpy.data.meshes.new(name); me.from_pydata(verts, edges, []); ob = bpy.data.objects.new(name, me)
        sc.collection.objects.link(ob)
        ob.modifiers.new('skin', 'SKIN')
        for i, r in enumerate(radii):
            ob.data.skin_vertices[0].data[i].radius = (r, r * .8)
        ob.data.skin_vertices[0].data[0].use_root = True
        sd = ob.modifiers.new('sub', 'SUBSURF'); sd.levels = 2; sd.render_levels = 2
        me.materials.append(m)
        return ob
    def person(x, h, arm_l='down', arm_r='down', hair='short', y=5):
        # joints (z up, facing +y away from camera); h = height scale
        P = lambda dx, dz, dy=0: (x + dx * h, y + dy * h, dz * h)
        V = [P(0, .95), P(0, 1.2), P(0, 1.42), P(0, 1.55),                      # 0 pelvis 1 spine 2 chest 3 neck
             P(-.2, 1.44), P(.2, 1.44),                                         # 4 L shoulder 5 R shoulder
             P(-.1, .9), P(-.12, .48), P(-.12, .05), P(.1, .9), P(.12, .48), P(.12, .05)]   # legs 6-11
        E = [(0, 1), (1, 2), (2, 3), (2, 4), (2, 5), (0, 6), (6, 7), (7, 8), (0, 9), (9, 10), (10, 11)]
        R = [.17, .15, .19, .07, .08, .08, .1, .075, .065, .1, .075, .065]
        def arm(si, side, pose):
            d = -1 if side == 'l' else 1
            if pose == 'down':   pts = [P(d * .27, 1.15), P(d * .3, .88)]
            elif pose == 'up':   pts = [P(d * .32, 1.78), P(d * .42, 2.12)]
            elif pose == 'hug':  pts = [P(d * .45, 1.46, .02), P(d * .78, 1.47, .04)]
            else:                pts = [P(d * .27, 1.2, -.05), P(d * .2, 1.0, -.1)]
            i0 = len(V); V.extend(pts); E.extend([(si, i0), (i0, i0 + 1)]); R.extend([.065, .055])
        arm(4, 'l', arm_l); arm(5, 'r', arm_r)
        skel(V, E, R, body, 'person')
        head = sphere(.13 * h, P(0, 1.72), body, 'head', 24); head.scale = (1, .95, 1.12)
        if hair == 'spiky':
            for k, (dx, dz, rx, ry) in enumerate(((-.1, 1.83, .5, -.6), (-.04, 1.88, .15, -.2), (.05, 1.87, -.1, .25), (.11, 1.82, -.4, .6), (0, 1.8, .9, 0), (-.13, 1.72, .2, -1.2), (.13, 1.72, .2, 1.2))):
                bpy.ops.mesh.primitive_cone_add(radius1=.055 * h, depth=.2 * h, location=P(dx, dz, .02), rotation=(rx, ry, 0), vertices=8)
                bpy.context.object.data.materials.append(body)
        elif hair == 'pony':
            cap = sphere(.14 * h, P(0, 1.75, .01), body, 'hair', 24); cap.scale = (1.05, 1, 1.02)
            skel([P(0, 1.78, .1), P(0, 1.62, .2), P(0, 1.42, .22)], [(0, 1), (1, 2)], [.06, .05, .025], body, 'pony')
        else:
            cap = sphere(.145 * h, P(0, 1.76, .01), body, 'hair', 24); cap.scale = (1.06, 1.02, .9)
    person(-.95, 1.0, 'down', 'hug', 'pony')
    person(0, 1.08, 'down', 'up', 'spiky')
    person(.95, 1.02, 'hug', 'down', 'short')
    star = mat('star', hexc('#ffd23f'), .3, emit=hexc('#ffe9a0'), estr=20); sphere(1.2, (16, 90, 40), star)
    c = camera((0, .2, 1.2), (0, 20, 2.9), 30)
    key_cam(c, [(1, (-.7, -.6, 1.0), (0, 20, 2.8)), (F, (.35, .6, 1.3), (0, 20, 3.3))])

elif CLIP == 'star':
    # the opportunity: a glowing star is handed up from the city, rising into the night sky
    flat_sky(hexc('#141a5c'), hexc('#3d6be8'), .8)
    city = mat('bld', hexc('#1b1f4a'), .9)
    lit = mat('lit', hexc('#232a6a'), .9, emit=hexc('#ffb86b'), estr=.25)
    for i in range(70):
        w, h = rnd.uniform(3, 7), rnd.uniform(4, 26)
        box((w, w, h), (rnd.uniform(-80, 80), rnd.uniform(16, 90), h / 2), rnd.choice([city, city, lit]))
    stm = mat('star', hexc('#ffd23f'), .3, emit=hexc('#ffc93a'), estr=2.2)
    # star shape: 5-point extruded
    import bmesh
    me = bpy.data.meshes.new('star'); bm = bmesh.new(); pts = []
    for k in range(10):
        r = 1.0 if k % 2 == 0 else .45; a = math.pi / 2 + k * math.pi / 5
        pts.append(bm.verts.new((math.cos(a) * r, 0, math.sin(a) * r)))
    f = bm.faces.new(pts); ex = bmesh.ops.extrude_face_region(bm, geom=[f])
    bmesh.ops.translate(bm, vec=(0, .35, 0), verts=[v for v in ex['geom'] if isinstance(v, bmesh.types.BMVert)])
    bm.to_mesh(me); obj = bpy.data.objects.new('star', me); sc.collection.objects.link(obj); me.materials.append(stm)
    bpy.ops.object.light_add(type='POINT'); pl = bpy.context.object; pl.data.energy = 900; pl.data.color = (1, .85, .45); pl.parent = obj
    small = mat('sstar', (1, 1, 1), .3, emit=hexc('#fff6c8'), estr=10)
    for i in range(80):
        sphere(rnd.uniform(.08, .2), (rnd.uniform(-60, 60), rnd.uniform(40, 120), rnd.uniform(25, 80)), small, 'sp', 8)
    for f_, z in ((1, 6), (F, 34)):
        obj.location = (0, 6, z); obj.rotation_euler = (0, f_ * .02, 0)
        obj.keyframe_insert('location', frame=f_); obj.keyframe_insert('rotation_euler', frame=f_)
    obj.scale = (2.2, 2.2, 2.2)
    c = camera((0, -8, 2), (0, 6, 8), 30)
    key_cam(c, [(1, (0, -9, 2.5), (0, 6, 7)), (F, (0, -12, 10), (0, 6, 33))])

elif CLIP == 'kmitl':
    # campus, time-lapse from late afternoon to night: sun sets, windows light up
    s, bg = sky('MULTIPLE_SCATTERING', 22, 210, .32)
    sn = sun(22, 210, 3.0, (1, .9, .78))
    for f_, e, st, en, col in ((1, 22, .1, 2.2, (1, .9, .78)), (int(F * .55), 1.5, .22, 1.0, (1, .55, .35)), (F, -6, .03, 0, (1, .5, .3))):
        s.sun_elevation = math.radians(e); s.keyframe_insert('sun_elevation', frame=f_)
        bg.inputs['Strength'].default_value = st; bg.inputs['Strength'].keyframe_insert('default_value', frame=f_)
        sn.data.energy = en; sn.data.keyframe_insert('energy', frame=f_)
        sn.rotation_euler = (math.radians(90 - max(e, 0)), 0, math.radians(210)); sn.keyframe_insert('rotation_euler', frame=f_)
    brick = mat('brick', hexc('#e39b7b'), .8); white = mat('white', hexc('#fff6ea'), .6)
    glassw = mat('win', hexc('#4f7fc4'), .2, .3, emit=hexc('#ffd98a'), estr=0)
    em_node = glassw.node_tree.nodes['Principled BSDF'].inputs['Emission Strength']
    for f_, v in ((1, 0), (int(F * .5), 0), (F, 4.5)):
        em_node.default_value = v; em_node.keyframe_insert('default_value', frame=f_)
    def tower(x, y, w, floors, d, rz):
        bpy.ops.object.empty_add(location=(x, y, 0), rotation=(0, 0, rz)); root = bpy.context.object
        fh = 3
        parts = [box((w, d, floors * fh + 1.2), (0, 0, (floors * fh + 1.2) / 2), brick)]
        for f in range(floors + 1): parts.append(box((w + .5, d + .5, .4), (0, 0, .4 + f * fh), white))
        cols = int(w / 1.6)
        for f in range(floors):
            for i in range(cols):
                parts.append(box((1.0, .15, 1.3), (-w / 2 + 1 + i * (w - 2) / (cols - 1), -d / 2 - .05, 2 + f * fh), glassw))
        for p in parts: p.parent = root
        return root
    tower(4, 30, 30, 9, 10, -.1); tower(-26, 22, 20, 4, 8, .4); tower(38, 34, 14, 5, 12, -.45)
    box((3.5, 11, 30), (19.5, 29, 15), white)
    ground = mat('grass', hexc('#6fcd5c'), .9); bpy.ops.mesh.primitive_plane_add(size=400); bpy.context.object.data.materials.append(ground)
    path = mat('path', hexc('#f1e2c8'), .9); box((6, 40, .05), (-3, -20, .03), path)
    leaf = [mat('l1', hexc('#55b964'), .8), mat('l2', hexc('#3f9f55'), .8)]; trunk = mat('trunk', hexc('#8a5a3c'), .8)
    for i in range(16): tree(-45 + i * 6 + rnd.uniform(-1, 1), 16 + rnd.uniform(-2, 2), 1.0 + rnd.uniform(0, .3), leaf, trunk)
    for x, y in ((-20, -2), (22, -1), (-28, 6), (30, 5)): tree(x, y, 1.4, leaf, trunk)
    # I LOVE KMITL
    red = mat('red', hexc('#e23a3a'), .45); wl = mat('letter', hexc('#fbfbfd'), .45)
    def text(t, x, z, size, m, rot=0):
        bpy.ops.object.text_add(location=(x, 0, z), rotation=(math.radians(90), 0, rot)); o = bpy.context.object
        o.data.body = t; o.data.extrude = .35; o.data.size = size; o.data.align_x = 'CENTER'
        o.data.materials.append(m); return o
    text('I', -10.4, 0, 4.4, wl); text('LO', -6.6, 2.1, 2.2, red); text('VE', -6.6, 0, 2.2, red); text('KMITL', 3.4, 0, 4.4, wl)
    fp = mat('pot', hexc('#2f7d3e'), .8)
    for i in range(7): box((1.1, .7, .4), (-9 + i * 3.1, -.9, .2), fp)
    # flag pole + flag with the Thai colours
    pole = mat('pole', hexc('#e9eef5'), .4, .6); cyl(.08, 13, (13, 6, 6.5), pole)
    for i, (z, col) in enumerate(((11.9, '#d9262e'), (11.4, '#ffffff'), (10.75, '#2a2f7f'), (10.1, '#ffffff'), (9.6, '#d9262e'))):
        hgt = .8 if col == '#2a2f7f' else .5
        box((4, .06, hgt), (15.05, 6, z - (0 if col != '#2a2f7f' else 0)), mat(f'f{i}', hexc(col), .7))
    c = camera((0, -22, 2.4), (0, 20, 9), 24)
    key_cam(c, [(1, (-5, -26, 2.2), (0, 20, 9.5)), (F, (2, -17, 2.8), (0, 20, 10.5))])


elif CLIP == 'team':
    # "not alone": a big line-up of original students in a sunflower field, the star mascot towering behind
    rmp, _ = flat_sky(hexc('#2a62d8'), hexc('#cfeaff'), 1.0)
    rmp.color_ramp.elements[0].position = .02; rmp.color_ramp.elements[1].position = .6
    sun(48, 200, 2.4)
    cm = mat('cloud', (1, 1, 1), .9, emit=(1, 1, 1), estr=.45)
    for x, y, z, s_ in ((-26, 60, 22, 6), (20, 70, 28, 7), (38, 55, 16, 5), (-6, 80, 34, 8)):
        cloud((x, y, z), s_, cm)
    ground = mat('field', hexc('#6fb04a'), .9); bpy.ops.mesh.primitive_plane_add(size=300); bpy.context.object.data.materials.append(ground)
    star_mascot((0, 9, 4.2), 4.2)
    # sunflowers: one master + linked duplicates
    stem = M('#3f8f3a', .3); pet = M('#ffc81f', .45); ctr = M('#6b3f1f', .3)
    GROUPS = {'far': [], 'mid': [], 'front': []}
    def flower(x, y, hgt, rz):
        g = 'front' if y < 0 else ('mid' if y < 4.4 else 'far')
        GROUPS[g].append(cyl(.05, hgt, (x, y, hgt / 2), stem, v=6))
        GROUPS[g].append(cyl(.34, .08, (x, y, hgt), pet, rot=(1.35, 0, rz), v=14))
        GROUPS[g].append(cyl(.17, .1, (x, y - .03, hgt), ctr, rot=(1.35, 0, rz), v=12))
    for i in range(150):
        flower(rnd.uniform(-16, 16), rnd.uniform(4.4, 11), rnd.uniform(1.6, 2.8), rnd.uniform(-.3, .3))
    for i in range(70):
        flower(rnd.uniform(-12, 12), rnd.uniform(2.0, 4.3), rnd.uniform(1.3, 2.1), rnd.uniform(-.3, .3))
    for i in range(46):
        flower(rnd.uniform(-10, 10), rnd.uniform(-3.6, -2.2), rnd.uniform(.45, 1.0), rnd.uniform(-.3, .3))
    cast = [
        dict(skin='#e8b894', top='#f4f4f4', bottom='#2b2f45', hair='#f0c14b', hair_style='spiky', arms=('hip', 'hip'), tie='#d62f3a', h=1.12, big=1.15),
        dict(skin='#f6d3bc', top='#9aa0b8', bottom='#1d2a3e', hair='#8f8ff0', hair_style='long', arms=('peace', 'peace'), tie='#d62f3a', h=.98),
        dict(skin='#c98d67', top='#ffcc33', bottom='#3a2d1d', hair='#1b1b1b', hair_style='bob', arms=('cross', 'cross'), h=1.02),
        dict(skin='#f1c9ab', top='#2e3c8f', bottom='#1b2244', hair='#1c2a55', hair_style='spiky', arms=('down', 'up'), h=1.04),
        dict(skin='#f4d2bb', top='#ffffff', bottom='#1f7a5a', hair='#39b37a', hair_style='bob', arms=('down', 'down'), tie='#d62f3a', h=.95),
        dict(skin='#e2b08e', top='#ff6000', bottom='#20294a', hair='#ff9f3d', hair_style='spiky', arms=('hip', 'down'), h=1.06),
        dict(skin='#f6d8c4', top='#6b3fa0', bottom='#221a3c', hair='#e9e9f5', hair_style='long', arms=('cross', 'cross'), h=.97),
        dict(skin='#d9a27f', top='#3fb4d8', bottom='#1b3b52', hair='#10253f', hair_style='spiky', arms=('up', 'down'), h=1.03),
        dict(skin='#f2c7a5', top='#e33b4f', bottom='#2a1b2e', hair='#5a2d1a', hair_style='bob', arms=('down', 'hip'), h=.99),
    ]
    xs = [0, -1.25, 1.25, -2.5, 2.5, -3.75, 3.75, -5.0, 5.0]
    ys = [0, .35, .35, .8, .8, 1.2, 1.2, 1.6, 1.6]
    for c_, x, y in zip(cast, xs, ys):
        hh = c_.pop('h'); human(x, y, hh * 1.7, rotz=-x * .03, **c_)
    if LAYER:
        keep = set(GROUPS['front']) if LAYER == 'front' else set(GROUPS['mid']) if LAYER == 'mid' else None
        drop = set(GROUPS['front'] + GROUPS['mid']) if LAYER == 'far' else None
        for o in list(sc.objects):
            if o.type in ('CAMERA', 'LIGHT'): continue
            if keep is not None and o not in keep: o.hide_render = True
            if drop is not None and o in drop: o.hide_render = True
        if LAYER in ('front', 'mid'): sc.view_settings.view_transform = 'Standard'
    c = camera((0, -10, 1.5), (0, 2, 2.3), 30)
    key_cam(c, [(1, (0, -11.5, 1.3), (0, 2, 2.4)), (F, (0, -9.2, 1.6), (0, 2, 2.25))])

elif CLIP == 'pass':
    # "passing the opportunity": a mentor stands in a blaze of golden light, a student kneels, speed lines rush past
    rmp, _ = flat_sky(hexc('#ffb347'), hexc('#fff0c0'), 1.25)
    ground = mat('ground', hexc('#e79a4a'), .9, emit=hexc('#e79a4a'), estr=.15); bpy.ops.mesh.primitive_plane_add(size=200); bpy.context.object.data.materials.append(ground)
    sun(20, 250, 3.0, (1, .8, .55))
    # a ruined wall behind them, washed out by the light
    wallm = mat('wall', hexc('#d8743a'), .9, emit=hexc('#f0a060'), estr=.25)
    for i in range(7):
        box((1.6, .6, rnd.uniform(2.5, 5)), (-5 + i * 1.7, 7, 1.5), wallm, rot=(0, 0, rnd.uniform(-.05, .05)))
    human(2.1, 0, 1.95, rotz=.35, skin='#8a5a44', top='#5a4a6a', bottom='#2b2240', hair='#c9962e', hair_style='wild', arms=('down', 'down'), big=1.25, face=False)
    human(-2.0, .4, 1.7, rotz=-.5, skin='#8a5a44', top='#1c2033', bottom='#1c2033', hair='#1f3b8a', hair_style='spiky', arms=('down', 'down'), legs='kneel', face=False)
    # speed lines
    nofs = bpy.data.collections.new('nofs'); sc.collection.children.link(nofs)
    ls.select_by_collection = True; ls.collection = nofs; ls.collection_negation = 'EXCLUSIVE'
    lm = mat('line', (1, 1, 1), .5, emit=hexc('#fff6dc'), estr=2.5)
    om = mat('line2', (1, 1, 1), .5, emit=hexc('#ff8a3d'), estr=3)
    for i in range(160):
        L = rnd.uniform(3, 11); m_ = lm if rnd.random() < .7 else om
        b = box((L, .015, rnd.uniform(.015, .05)), (0, 0, 0), m_, rot=(0, math.radians(-18), 0), name='sl')
        for col in b.users_collection: col.objects.unlink(b)
        nofs.objects.link(b)
        x0, z0, yy = rnd.uniform(-12, 8), rnd.uniform(-.5, 6), rnd.uniform(-2.5, 5)
        dx = rnd.uniform(10, 22)
        for f_, off in ((1, 0), (F, 1)):
            b.location = (x0 + off * dx * .95, yy, z0 - off * dx * .31)
            b.keyframe_insert('location', frame=f_)
        if b.animation_data and hasattr(b.animation_data.action, 'fcurves'):
            for fc in b.animation_data.action.fcurves:
                for k in fc.keyframe_points: k.interpolation = 'LINEAR'
    c = camera((0, -9, 1.3), (0, 2, 1.5), 30)
    key_cam(c, [(1, (-.6, -9.6, 1.2), (0, 2, 1.45)), (F, (.4, -8.4, 1.4), (0, 2, 1.6))])

elif CLIP == 'fist':
    # "you can be one too": a mentor at sunset thrusts his fist straight at the viewer
    rmp, _ = flat_sky(hexc('#d9482a'), hexc('#ffc44a'), 1.0)
    rmp.color_ramp.elements[0].position = .05; rmp.color_ramp.elements[1].position = .7
    sd = mat('sundisc', (1, 1, 1), .5, emit=hexc('#fff3c2'), estr=12); sphere(5, (-14, 40, 4), sd)
    sun(6, 60, 2.2, (1, .7, .4))
    bpy.ops.object.light_add(type='AREA', location=(0, -6, 3), rotation=(math.radians(-70), 0, 0)); fl = bpy.context.object; fl.data.energy = 110; fl.data.color = (1, .78, .55); fl.data.size = 5
    leaf = [M('#3e7a3a', .25), M('#58963f', .3)]; trunk = M('#4b3020', .2)
    for x, y, s_ in ((10, 18, 2.4), (15, 22, 2.8), (7, 26, 2.1), (-18, 30, 2.2)):
        tree(x, y, s_, leaf, trunk)
    cm = mat('cloud', hexc('#ff9a6a'), .9, emit=hexc('#ffb08a'), estr=1.0)
    for x, y, z, s_ in ((-10, 50, 16, 5), (12, 55, 20, 6), (4, 60, 26, 7)):
        cloud((x, y, z), s_, cm)
    hero = human(.55, 1.5, 2.4, rotz=-.6, skin='#e3a57a', top='#ff6000', bottom='#1d2a55', hair='#f5c542', hair_style='wild',
                 arms=('down', 'fist'), stripe='#2f6fe0', big=1.35)
    for f_, rz in ((1, -.62), (F, -.5)):
        hero.rotation_euler = (0, 0, rz); hero.keyframe_insert('rotation_euler', frame=f_)
    c = camera((0, -4.2, 2.7), (0, 1.5, 3.6), 30)
    key_cam(c, [(1, (-.8, -4.9, 2.5), (.2, 1.5, 3.55)), (F, (.2, -3.9, 2.75), (.2, 1.5, 3.65))])

# ---------------------------------------------------------------- XFER: scroll-scrubbed camera moves that CONNECT two scenes
# 1 towers -> fly into a lit window that shows the desk room   2 desk -> code on the laptop becomes the meadow, push into the screen
# 3 kmitl  -> start on a campus screen showing the meadow, pull back to the campus   4 kmitl night -> tilt up into the starry sky (dawn follows)
XF = os.environ.get('XFER')
if XF:
    XT = '/tmp/claude-0/-home-claude/fed940bd-495e-598e-8150-238c153e3d70/scratchpad/xt/'
    N = int(os.environ.get('XN', '32')); sc.frame_start, sc.frame_end = 1, N
    if os.environ.get('FSTART'): sc.frame_start = int(os.environ['FSTART'])
    if os.environ.get('FEND'): sc.frame_end = int(os.environ['FEND'])
    OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out', f'x{XF}-{ORIENT}'); os.makedirs(OUT, exist_ok=True)
    P = ORIENT == 'p'
    c.animation_data_clear()
    if c.data.animation_data: c.data.animation_data_clear()
    c.data.sensor_fit = 'AUTO'; c.data.sensor_width = 36
    def emit_img(path, strength=1.0):
        m = bpy.data.materials.new('portal'); m.use_nodes = True; nt = m.node_tree
        for n in list(nt.nodes):
            if n.type != 'OUTPUT_MATERIAL': nt.nodes.remove(n)
        t = nt.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(path); t.extension = 'EXTEND'
        e = nt.nodes.new('ShaderNodeEmission'); e.inputs['Strength'].default_value = strength
        nt.links.new(t.outputs['Color'], e.inputs['Color']); nt.links.new(e.outputs[0], nt.nodes['Material Output'].inputs['Surface'])
        return m
    def portal(path, loc, rz, L):
        w, h = (L * 9 / 16, L) if P else (L, L * 9 / 16)
        bpy.ops.mesh.primitive_plane_add(size=1, location=loc, rotation=(math.radians(90), 0, rz)); o = bpy.context.object
        o.scale = (w * 1.02, h * 1.02, 1); o.data.materials.append(emit_img(path)); return o, w, h
    def keys(frames, lens=None):
        for f, loc, look in frames:
            c.location = loc; aim(c, look)
            c.keyframe_insert('location', frame=f); c.keyframe_insert('rotation_euler', frame=f)
        if lens:
            for f, v in lens: c.data.lens = v; c.data.keyframe_insert('lens', frame=f)
        for ad in (c.animation_data, c.data.animation_data):
            act = ad and ad.action
            for fc in (act.fcurves if act and hasattr(act, 'fcurves') else []):
                for k in fc.keyframe_points: k.interpolation = 'BEZIER'; k.handle_left_type = k.handle_right_type = 'AUTO_CLAMPED'
    if XF == '1' and CLIP == 'towers':
        L = 2.4 if P else 3.4; lens = 24; d = (L / 2) * lens / 18
        cx, cz, py = -8.6, 5.1, -6.33
        portal(XT + f'desk-{ORIENT}.png', (cx, py, cz), 0, L)
        keys([(1, (0, -36, 2.6), (0, 0, 22)), (int(N * .5), (-5, -24, 3.6), (cx, 0, 8)), (N, (cx, py - d, cz), (cx, 0, cz))], [(1, 15), (N, lens)])
    elif XF == '2' and CLIP == 'desk':
        # blend the code into the meadow on the laptop screen, then push in until the screen is the frame
        nt = sm.node_tree; e1 = [n for n in nt.nodes if n.type == 'EMISSION'][0]
        t2 = nt.nodes.new('ShaderNodeTexImage'); t2.image = bpy.data.images.load(XT + f'scr-{ORIENT}.png')
        e2 = nt.nodes.new('ShaderNodeEmission'); e2.inputs['Strength'].default_value = 1.0
        mx = nt.nodes.new('ShaderNodeMixShader'); out = nt.nodes['Material Output']
        nt.links.new(t2.outputs['Color'], e2.inputs['Color']); nt.links.new(e1.outputs[0], mx.inputs[1]); nt.links.new(e2.outputs[0], mx.inputs[2])
        nt.links.new(mx.outputs[0], out.inputs['Surface'])
        for f, v in ((1, 0), (int(N * .15), 0), (int(N * .5), 1), (N, 1)): mx.inputs[0].default_value = v; mx.inputs[0].keyframe_insert('default_value', frame=f)
        lens = 31.5 if P else 30; th = math.radians(78)
        n = Vector((0, -math.sin(th), math.cos(th))); ctr = Vector((0, .33, 1.63))
        d = (.92 / 2 if P else 1.45 / 2) * lens / 18
        fin = ctr + n * d
        keys([(1, CAM_B, LOOK_B), (int(N * .45), (.2, -3.4, 1.85), (0, .3, 1.6)), (N, tuple(fin), tuple(ctr))], [(1, 28 if not P else 29.4), (int(N * .45), lens), (N, lens)])
    elif XF in ('3', '4') and CLIP == 'kmitl':
        for idb in (sc.world.node_tree, sn, sn.data, glassw.node_tree):
            if idb.animation_data: idb.animation_data_clear()
        lens = 25.2 if P else 24
        if XF == '3':
            s.sun_elevation = math.radians(22); bg.inputs['Strength'].default_value = .1; sn.data.energy = 2.2; em_node.default_value = 0
            L = 8.0; d = (L / 2) * lens / 18; bx, by, bz = -22, -24, (4.5 if P else 4)
            o, w, h = portal(XT + f'bb-{ORIENT}.png', (bx, by, bz), math.radians(90), L)
            fr = mat('bbframe', hexc('#1d2233'), .5)
            box((.3, w + .6, .3), (bx - .2, by, bz + h / 2 + .15), fr); box((.3, w + .6, .3), (bx - .2, by, bz - h / 2 - .15), fr)
            box((.3, .3, h + .6), (bx - .2, by - w / 2 - .15, bz), fr); box((.3, .3, h + .6), (bx - .2, by + w / 2 + .15, bz), fr)
            for yy in (by - w / 3, by + w / 3): cyl(.18, bz - h / 2, (bx - .3, yy, (bz - h / 2) / 2), fr)
            keys([(1, (bx + d, by, bz), (bx, by, bz)), (int(N * .42), (bx + 17, by - 4, bz + .6), (bx, by, bz)), (N, (-5, -26, 2.2), (0, 20, 9.5))], [(1, lens), (N, lens)])
        else:
            em_node.default_value = 4.5
            for f, e, st, en in ((1, -6, .03, 0), (N, 0.5, .1, .25)):
                s.sun_elevation = math.radians(e); s.keyframe_insert('sun_elevation', frame=f)
                bg.inputs['Strength'].default_value = st; bg.inputs['Strength'].keyframe_insert('default_value', frame=f)
                sn.data.energy = en; sn.data.keyframe_insert('energy', frame=f)
            nofs = bpy.data.collections.new('nofs'); sc.collection.children.link(nofs)
            ls.select_by_collection = True; ls.collection = nofs; ls.collection_negation = 'EXCLUSIVE'
            stm = mat('star', (1, 1, 1), .5, emit=hexc('#fff6dc'), estr=8)
            for i in range(260):
                az = rnd.uniform(-1.3, 1.3); el = rnd.uniform(.35, 1.45); R = 180
                p = (math.sin(az) * math.cos(el) * R, math.cos(az) * math.cos(el) * R, math.sin(el) * R + 10)
                o = sphere(rnd.uniform(.25, .6), p, stm, seg=6)
                for col in o.users_collection: col.objects.unlink(o)
                nofs.objects.link(o)
            keys([(1, (2, -17, 2.8), (0, 20, 10.5)), (N, (2, -20, 3.4), (1, 12, 75))], [(1, lens), (N, lens)])
    elif XF == '5' and CLIP == 'kmitl':
        # one continuous shot: sunset time-lapse on campus -> windows light up -> stars fade in -> crane up + zoom into a star cluster
        for idb in (sc.world.node_tree, sn, sn.data, glassw.node_tree):
            if idb.animation_data: idb.animation_data_clear()
        lens = 25.2 if P else 24
        for f, e, st, en, win in ((1, 22, .1, 2.2, 0), (16, 8, .16, 1.6, 0), (26, 1.5, .2, 1.0, .6), (38, -6, .03, 0, 4.5), (N, -7, .025, 0, 4.5)):
            s.sun_elevation = math.radians(e); s.keyframe_insert('sun_elevation', frame=f)
            bg.inputs['Strength'].default_value = st; bg.inputs['Strength'].keyframe_insert('default_value', frame=f)
            sn.data.energy = en; sn.data.keyframe_insert('energy', frame=f)
            sn.rotation_euler = (math.radians(90 - max(e, 0)), 0, math.radians(210)); sn.keyframe_insert('rotation_euler', frame=f)
            em_node.default_value = win; em_node.keyframe_insert('default_value', frame=f)
        nofs = bpy.data.collections.new('nofs'); sc.collection.children.link(nofs)
        ls.select_by_collection = True; ls.collection = nofs; ls.collection_negation = 'EXCLUSIVE'
        def star_mat(name, col, peak, f0, f1):
            m = mat(name, (0, 0, 0), .5, emit=hexc(col), estr=0); m['f0'] = f0
            es = m.node_tree.nodes['Principled BSDF'].inputs['Emission Strength']
            for f, v in ((1, 0), (f0, 0), (f1, peak), (N, peak)): es.default_value = v; es.keyframe_insert('default_value', frame=f)
            return m
        # stars appear in waves: a few bright ones first, then the field, then the faint cluster we zoom into
        waves = [star_mat('st_a', '#fff3cf', 12, 30, 40), star_mat('st_b', '#ffffff', 8, 34, 48), star_mat('st_c', '#dfe8ff', 7, 40, 56)]
        def put(az, el, r, m):
            R = 180; p = (math.sin(az) * math.cos(el) * R, math.cos(az) * math.cos(el) * R, math.sin(el) * R + 10)
            o = sphere(r, p, m, seg=6)
            for col in o.users_collection: col.objects.unlink(o)
            nofs.objects.link(o)
            for f, h in ((1, True), (int(m['f0']) + 1, False)): o.hide_render = h; o.keyframe_insert('hide_render', frame=f)
        for i in range(240): put(rnd.uniform(-1.3, 1.3), rnd.uniform(.3, 1.45), rnd.uniform(.22, .5), waves[1])
        for i in range(140): put(rnd.gauss(.06, .22), rnd.gauss(.63, .12), rnd.uniform(.14, .32), waves[2])
        for i in range(10): put(rnd.uniform(-.5, .6), rnd.uniform(.32, .85), rnd.uniform(.55, .8), waves[0])
        keys([(1, (-5, -26, 2.2), (0, 20, 9.5)), (24, (2, -17, 2.8), (0, 20, 10.5)), (34, (2.4, -16, 3.3), (.6, 20, 12.5)),
              (N, (4, -10, 10), (8, 60, 61))], [(1, lens), (34, lens), (N, lens * 1.75)])

if os.environ.get('TALL') and CLIP == 'towers':
    # one tall still of the towers for the layered parallax hero (sky keyed out, clouds live in CSS behind)
    TW, TH = [int(v) for v in os.environ['TALL'].split('x')]
    sc.render.resolution_x, sc.render.resolution_y = TW, TH
    c.animation_data_clear(); c.data.sensor_fit = 'VERTICAL'; c.data.lens = float(os.environ.get('LENS', '13'))
    c.location = (0, float(os.environ.get('TCY', '-30')), float(os.environ.get('TCZ', '2.2'))); aim(c, (0, 0, float(os.environ.get('LOOKZ', '50'))))
    if os.environ.get('SHIFT'): aim(c, (0, 0, c.location.z)); c.data.shift_y = float(os.environ['SHIFT'])
    sc.render.line_thickness = float(os.environ.get('LINE', '2')); sc.cycles.samples = 24
    if os.environ.get('DETAIL'):
        # extra dressing for the hero towers: edge light strips, rooftop beacons, lit lobby, bushes, lamps, flags
        strip = mat('strip', hexc('#8ff0ff'), .3, emit=hexc('#8ff0ff'), estr=3.5)
        beacon = mat('beacon', hexc('#ff4d5e'), .3, emit=hexc('#ff4d5e'), estr=10)
        for side in (-1, 1):
            cx = side * 9.5
            for ex in (-7.2, 7.2):
                box((.22, .22, 76), (cx + ex, -6.25, 38.5), strip)
            for ex in (-3, 3): sphere(.45, (cx + side * 2 + ex * .2, 1, 90.4), beacon, seg=10)
            box((12, .15, .6), (cx, -6.3, 77.2), strip)
        lobby = mat('lobby', hexc('#ffe2a0'), .3, emit=hexc('#ffcf7a'), estr=2.2)
        box((44, .2, 5.2), (0, -9.6, 3.9), lobby)
        door = mat('door', hexc('#2f6fb8'), .1, .6, emit=hexc('#9fd0ff'), estr=.6)
        box((6, .3, 4.2), (0, -9.8, 3.3), door)
        bush = [mat('b1', hexc('#4fae5a'), .8), mat('b2', hexc('#6cc36b'), .8)]
        for i in range(22):
            x = -26 + i * 2.5 + rnd.uniform(-.4, .4); o = sphere(rnd.uniform(.9, 1.3), (x, -13.2, .7), rnd.choice(bush), seg=12); o.scale = (1.2, .9, .8)
    if os.environ.get('UNDER'):
        # cut-away diorama: the street is sliced open at y=FY, showing soil, pipes, cables and lamps under the towers
        FY = -34.0
        bpy.data.objects.remove(GROUND, do_unlink=True)
        grass = mat('grass2', hexc('#8fcf6e'), .9)
        box((240, 300, 1.0), (0, FY + 150, -.5), grass)                           # the lawn, only behind the cut
        side = mat('side', hexc('#d9dde6'), .7); curb = mat('curb', hexc('#aeb4c4'), .7)
        box((240, 3.2, .7), (0, FY + 1.6, .35), side); box((240, .5, .8), (0, FY + .25, .4), curb)
        soils = [('#8a5236', 0, -2.4), ('#7a4431', -2.4, -6.5), ('#6a3a3e', -6.5, -11), ('#52304c', -11, -16), ('#3a2244', -16, -21), ('#1e1428', -21, -34)]
        for i, (col, z0, z1) in enumerate(soils):
            box((240, 60, z0 - z1), (0, FY + 30, (z0 + z1) / 2 - .5), mat(f'soil{i}', hexc(col), .95, emit=hexc(col), estr=.55))

        for i, (col, z0, z1) in enumerate(soils[:-1]):             # wavy strata: blobs of each layer spill over the next boundary
            m_ = bpy.data.materials.get(f'soil{i}')
            x = -70
            while x < 70:
                w_ = rnd.uniform(3, 8); o = sphere(1, (x + w_, FY + .02, z1 - .5 + rnd.uniform(-.4, .5)), m_, seg=16); o.scale = (w_, .05, rnd.uniform(.6, 1.6)); x += w_ * rnd.uniform(1.4, 2.2)
        rock = mat('rock', hexc('#4a3a52'), .9); rock2 = mat('rock2', hexc('#6b5a6e'), .9)
        for i in range(40):
            o = sphere(rnd.uniform(.35, 1.1), (rnd.uniform(-60, 60), FY - .1, rnd.uniform(-24, -1.5)), rnd.choice([rock, rock2]), seg=10); o.scale = (1, .35, .7)
        for i in range(14):
            L_ = rnd.uniform(1.6, 4.2); cyl(.12, L_, (rnd.uniform(-55, 55), FY - .05, -.2 - L_ / 2), mat('root', hexc('#b0763e'), .8, emit=hexc('#b0763e'), estr=.4), rot=(0, rnd.uniform(-.35, .35), 0), v=6)
        gem = [mat('gemb', hexc('#5fb8ff'), .2, emit=hexc('#5fb8ff'), estr=2.5), mat('gemp', hexc('#b07bff'), .2, emit=hexc('#b07bff'), estr=2.5)]
        for i in range(7):
            bpy.ops.mesh.primitive_ico_sphere_add(radius=rnd.uniform(.45, .8), subdivisions=1, location=(rnd.uniform(-50, 50), FY - .2, rnd.uniform(-20, -8)))
            o = bpy.context.object; o.scale = (.7, .5, 1.3); o.data.materials.append(rnd.choice(gem))
        pipe = mat('pipe', hexc('#6f7688'), .45, .5); band = mat('band', hexc('#9a5a2e'), .6, .3)
        for x0, x1, z in ((-62, -24, -3.4), (26, 62, -4.2), (-62, -38, -12)):
            L = x1 - x0; cyl(1.25, L, ((x0 + x1) / 2, FY - .4, z), pipe, rot=(0, math.radians(90), 0), v=20)
            for k in range(3): cyl(1.42, .6, (x0 + 3 + k * (L - 6) / 2, FY - .4, z), band, rot=(0, math.radians(90), 0), v=20)
        cyl(1.25, 10, (33, FY - .4, -9.2), pipe, v=20); cyl(1.42, .6, (33, FY - .4, -6.5), band, v=20)
        def cable(pts, col, r=.32, rough=.35, name='cab'):
            cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = r; cu.bevel_resolution = 4; cu.use_fill_caps = True
            sp = cu.splines.new('BEZIER'); sp.bezier_points.add(len(pts) - 1)
            for bp, p in zip(sp.bezier_points, pts): bp.co = p; bp.handle_left_type = bp.handle_right_type = 'AUTO'
            o = bpy.data.objects.new(name, cu); sc.collection.objects.link(o)
            o.data.materials.append(mat('c' + col + name, hexc(col), rough, emit=hexc(col), estr=.35)); return o
        y = FY - .9
        clip = mat('clip', hexc('#2a2f45'), .5, .4); copper = mat('copper', hexc('#e08a3a'), .3, .8, emit=hexc('#ff9a3a'), estr=.6)
        # conduit bundle along the ceiling, clipped every few metres
        for dz, col in ((0, '#3a4058'), (.75, '#4a5070')):
            cable([(-40, y + .3, -1.9 - dz), (0, y + .3, -2.1 - dz), (40, y + .3, -1.9 - dz)], col, .2, .6, 'duct')
        for x in range(-30, 31, 10): box((.5, .6, 1.9), (x, y - .1, -2.4), clip)
        # broken orange cable: two ends droop towards each other with frayed copper tips (sparks are added on the page)
        cable([(-40, y - .3, -4.2), (-24, y - .3, -8.6), (-13, y - .3, -11.2), (-7.4, y - .3, -12.6)], '#ff8a3d', .26, .3, 'orL')
        cable([(40, y - .3, -4.0), (24, y - .3, -9.0), (8, y - .3, -12.4), (2.2, y - .3, -13.8)], '#ff8a3d', .26, .3, 'orR')
        for (x, z, rz) in ((-7.4, -12.6, -.35), (2.2, -13.8, .45)):
            for k in range(5):
                cyl(.07, .9, (x + (k - 2) * .12, y - .35, z + rnd.uniform(-.2, .2)), copper, rot=(0, math.radians(90) + rnd.uniform(-.7, .7), 0), v=5)
            cyl(.34, .3, (x, y - .3, z), clip, rot=(0, math.radians(90) + rz, 0), v=14)
        # purple cable, low and calm
        cable([(-40, y + .2, -9.5), (-18, y + .2, -15.2), (0, y + .2, -16.0), (18, y + .2, -15.0), (40, y + .2, -9.2)], '#8f6bff', .22, .35, 'pur')
        # clamps where the hamster's teal cable (drawn live on the page) is fixed
        for x in (-21.0, 24.0):
            cyl(.06, 3.6, (x, y - .1, -2.2 - 1.8), clip, v=6)
            box((.8, .9, .7), (x, y - .6, -6.0), clip); sphere(.18, (x, y - 1.1, -6.0), mat('bolt', hexc('#c7d0e2'), .3, .8), seg=8)
        glass = mat('bulb', hexc('#ffc94a'), .3, emit=hexc('#ffb52e'), estr=2.6); cage = mat('cage', hexc('#3a3040'), .6)
        for x, drop in ((-28, 1.6), (-9.5, 2.2), (9.5, 1.8), (28, 2.4), (-15.5, 1.2), (15.5, 1.4)):
            cyl(.07, drop, (x, y - .2, -2.6 - drop / 2), cage, v=6)
            bz = -2.6 - drop - .75
            sphere(.72, (x, y - .2, bz), glass, seg=14)
            cyl(.66, .4, (x, y - .2, bz + .72), cage, v=12)
            for a_ in (-1, 1): cyl(.05, 1.5, (x + a_ * .72, y - .7, bz), cage, v=5)
            bpy.ops.object.light_add(type='POINT', location=(x, FY - 2.5, bz)); l = bpy.context.object; l.data.energy = 220; l.data.color = (1, .78, .45); l.data.shadow_soft_size = .5

        # the hamster's teal cable (3D, thin): from clamp to clamp with a dip where the hamster hangs
        cable([(-40, y - .5, -3.2), (-21, y - .5, -6.0), (8.5, y - .5, -9.4), (24, y - .5, -6.2), (40, y - .5, -3.4)], '#3fc6e0', .24, .3, 'teal')
        # details: glowing mushrooms, a fossil bone, a junction box, dangling wire ties
        shroom = [mat('mc1', hexc('#ff7fb0'), .4, emit=hexc('#ff7fb0'), estr=1.4), mat('mc2', hexc('#8ff0ff'), .4, emit=hexc('#8ff0ff'), estr=1.4)]
        stem = mat('stem', hexc('#fff4e2'), .6, emit=hexc('#fff4e2'), estr=.4)
        for cx, cz, n in ((-30, -17.8, 3), (26, -16.6, 4), (-4, -20.2, 3), (13, -19.4, 2)):
            for i in range(n):
                x = cx + i * .9 + rnd.uniform(-.2, .2); h = rnd.uniform(.5, 1.1); m_ = shroom[(i + int(cx)) % 2]
                cyl(.11, h, (x, FY - .3, cz + h / 2), stem, v=8); o = sphere(.42 + rnd.uniform(0, .2), (x, FY - .3, cz + h), m_, seg=12); o.scale = (1, .6, .55)
        bone = mat('bone', hexc('#efe6d6'), .7, emit=hexc('#efe6d6'), estr=.25)
        for bx, bz, rot in ((-19, -13.6, .3), (30, -21.5, -.4)):
            cyl(.22, 2.4, (bx, FY - .1, bz), bone, rot=(0, math.radians(90) + rot, 0), v=10)
            for e in (-1, 1):
                for d in (-1, 1): sphere(.34, (bx + e * 1.15 * math.cos(rot), FY - .1, bz - e * 1.15 * math.sin(rot) + d * .22), bone, seg=10)
        jb = mat('jbox', hexc('#3c4466'), .5, .3); led = mat('led', hexc('#57e6a8'), .3, emit=hexc('#57e6a8'), estr=6)
        box((2.4, .8, 1.8), (27.5, FY - .6, -8.4), jb); sphere(.16, (26.8, FY - 1.05, -8.0), led, seg=8); sphere(.16, (27.4, FY - 1.05, -8.0), mat('led2', hexc('#ffd23f'), .3, emit=hexc('#ffd23f'), estr=6), seg=8)
        box((1.6, .1, .12), (27.5, FY - 1.02, -8.8), mat('slot', hexc('#1b1540'), .8))
        for x in (-33, -3, 24):
            cyl(.05, 1.2, (x, FY - .95, -2.9), mat('tie', hexc('#e33b4f'), .5), v=5)
        # soil speckle
        spk = [mat('sp1', hexc('#a8704a'), .9, emit=hexc('#a8704a'), estr=.5), mat('sp2', hexc('#3a2436'), .9), mat('sp3', hexc('#7a5a88'), .9, emit=hexc('#7a5a88'), estr=.4)]
        for i in range(260):
            z = rnd.uniform(-22, -1); o = sphere(rnd.uniform(.08, .22), (rnd.uniform(-34, 34), FY - .05, z), spk[0] if z > -8 else rnd.choice(spk[1:]), seg=6); o.scale = (1, .3, 1)
        bpy.ops.object.light_add(type='AREA', location=(0, FY - 30, -6), rotation=(math.radians(90), 0, 0)); fl = bpy.context.object
        fl.data.energy = 5000; fl.data.size = 120; fl.data.color = (1, .92, .85)
        # grass tufts along the lawn edge
        tuft = [mat('t1', hexc('#6cc36b'), .8, emit=hexc('#6cc36b'), estr=.8), mat('t2', hexc('#8fcf6e'), .8, emit=hexc('#8fcf6e'), estr=.8)]
        for i in range(90):
            x = rnd.uniform(-70, 70)
            bpy.ops.mesh.primitive_cone_add(radius1=rnd.uniform(.35, .7), depth=rnd.uniform(.8, 1.6), vertices=5, location=(x, FY + 3.6, .5))
            bpy.context.object.data.materials.append(rnd.choice(tuft)); bpy.context.object.location.y = FY + .4
        # straight-on orthographic view of the cut: nothing above the lawn is drawn (the page's towers sit on top)
        for o in list(sc.objects):
            if o.type != 'MESH' and o.type != 'CURVE': continue
            zmin = min((o.matrix_world @ Vector(v)).z for v in o.bound_box)
            ymin = min((o.matrix_world @ Vector(v)).y for v in o.bound_box)
            zmax = max((o.matrix_world @ Vector(v)).z for v in o.bound_box)
            if zmin > 0.45 or ymin > FY + 5 or (zmax > 2.2 and ymin > FY - 2 and o.name.startswith(('Cyl', 'cyl', 'box')) and zmin > -1): o.hide_render = True
        c.data.type = 'ORTHO'; c.data.sensor_fit = 'HORIZONTAL' if ORIENT == 'w' else 'VERTICAL'
        c.data.ortho_scale = float(os.environ.get('UW', '96'))
        c.location = (float(os.environ.get('UX', '0')), FY - 60, float(os.environ.get('UZ', '-17'))); c.rotation_euler = (math.radians(90), 0, 0)


# ---------------------------------------------------------------- bloom (compositor glare)
try:
    ng = bpy.data.node_groups.new('comp', 'CompositorNodeTree')
    rl = ng.nodes.new('CompositorNodeRLayers'); gl = ng.nodes.new('CompositorNodeGlare'); out = ng.nodes.new('NodeGroupOutput')
    ng.interface.new_socket('Image', in_out='OUTPUT', socket_type='NodeSocketColor')
    try: gl.inputs['Type'].default_value = 'Bloom'
    except Exception:
        try: gl.glare_type = 'BLOOM'
        except Exception: gl.glare_type = 'FOG_GLOW'
    for nm, v in (('Threshold', 1.6 if CLIP == 'kmitl' else .85), ('Strength', .6), ('Size', .5)):
        try: gl.inputs[nm].default_value = v
        except Exception: pass
    ng.links.new(rl.outputs['Image'], gl.inputs['Image']); ng.links.new(gl.outputs['Image'], out.inputs[0])
    if not os.environ.get('LAYER'): sc.compositing_node_group = ng
    print('bloom ok')
except Exception as e:
    print('bloom skipped', e)

# ---------------------------------------------------------------- render
if os.environ.get('STEP'): sc.frame_step = int(os.environ['STEP'])
if MODE == 'still':
    sc.frame_set(FR or 1)
    sc.render.filepath = os.path.join(OUT, f'still_{FR or 1:03d}.png')
    bpy.ops.render.render(write_still=True)
else:
    sc.render.filepath = os.path.join(OUT, 'f')
    bpy.ops.render.render(animation=True)
