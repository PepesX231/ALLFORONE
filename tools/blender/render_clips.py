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
sc.render.resolution_x, sc.render.resolution_y = W, H
sc.render.film_transparent = False
sc.view_settings.view_transform = 'Standard'
sc.view_settings.look = 'None'
sc.render.image_settings.file_format = 'PNG'
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
    ground = mat('ground', hexc('#8fcf6e'), .9); bpy.ops.mesh.primitive_plane_add(size=400, location=(0, 0, 0)); bpy.context.object.data.materials.append(ground)
    pinks = [mat('p1', hexc('#f7a8c4'), .7), mat('p2', hexc('#fbc2d6'), .7), mat('p3', hexc('#f590b5'), .7)]
    trunk = mat('trunk', hexc('#6b3f33'), .8)
    for x, y, s in ((-22, -22, 2.2), (-15, -30, 1.8), (21, -24, 2.3), (14, -31, 1.7), (-27, -12, 1.9), (27, -13, 2.0)):
        tree(x, y, s, pinks, trunk)
    cm = mat('cloud', (1, 1, 1), .9, emit=(1, 1, 1), estr=.45)
    for x, y, z, s in ((-60, 90, 70, 9), (40, 110, 95, 11), (80, 60, 55, 7), (-20, 140, 120, 12), (-90, 70, 40, 8), (-38, 25, 118, 7), (46, 35, 135, 8), (-70, 40, 160, 9), (60, 10, 105, 6), (-45, 5, 210, 14), (40, 20, 240, 16), (-5, -15, 280, 18), (75, 0, 200, 13), (-85, 25, 250, 15), (15, 40, 190, 11)):
        cloud((x, y, z), s, cm)
    if MODE == 'idle':
        for o in CLOUDS:
            x0 = o.location.x; o.location.x = x0 - 16; o.keyframe_insert('location', frame=1)
            o.location.x = x0 + 16; o.keyframe_insert('location', frame=F)
    petals((0, -30, 30), (30, 15, 1), 700, F, pinks[1])
    c = camera((0, -26, 2), (0, 0, 60), 15)
    key_cam(c, [(1, (0, -24, 2.0), (0, 0, 95)), (F, (0, -36, 2.6), (0, 0, 22))] if MODE != 'idle' else [(1, (0, -24, 2.0), (0, 0, 95)), (F, (0, -24, 2.0), (0, 0, 95))])

elif CLIP == 'desk':
    flat_sky(hexc('#0d1438'), hexc('#1b1f4a'), .6)
    bpy.ops.object.light_add(type='AREA', location=(0, -4, 4), rotation=(math.radians(-60), 0, 0)); fl = bpy.context.object; fl.data.energy = 120; fl.data.color = (.45, .55, 1); fl.data.size = 6
    wood = mat('wood', hexc('#7a4f38'), .55)
    box((6, 3, .12), (0, 0, 1), wood)
    for x in (-2.8, 2.8): box((.12, 2.8, 1), (x, 0, .5), wood)
    wall = mat('wall', hexc('#232a5e'), .9); box((12, .2, 6), (0, 1.8, 3), wall)
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
    c = camera((0, -3.6, 1.9), (0, .3, 1.6), 30)
    key_cam(c, [(1, (-.6, -3.9, 2.0), (0, .3, 1.55)), (F, (.25, -2.9, 1.75), (0, .3, 1.6))])

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
    sc.compositing_node_group = ng
    print('bloom ok')
except Exception as e:
    print('bloom skipped', e)

# ---------------------------------------------------------------- render
if MODE == 'still':
    sc.frame_set(FR or 1)
    sc.render.filepath = os.path.join(OUT, f'still_{FR or 1:03d}.png')
    bpy.ops.render.render(write_still=True)
else:
    sc.render.filepath = os.path.join(OUT, 'f')
    bpy.ops.render.render(animation=True)
