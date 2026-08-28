"""Close the end of the street with buildings, so the vista ends on a town.

WHY. Every shot down the canyon has a pale void where the street stops and the
board begins - and no camera position fixes it, because it is not a framing
problem. A real street ends on something: a cross street, a terminating block,
another row. This places that row.

Named HERO_End* so it lifts out with the rest of the dressing and the street
goes back to being exactly what the gate measured.

Run LOCALLY - it places baked meshes, which goes over MCP.
"""
import sys, os, json, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _path  # noqa: F401
import ue, recipes, stagegeo, palette

S = 'editor_toolset.toolsets.scene.SceneTools'
A = 'editor_toolset.toolsets.actor.ActorTools'
O = 'editor_toolset.toolsets.object.ObjectTools'
Z = stagegeo.FLOOR_Z
BAKED = '/Game/Stacktown/Baked'

# across the end of the street, facing back down it
END_X = 19400.0
Y_FROM, Y_TO = -24900.0, -20300.0
# a terminating block reads best as a WALL of frontage: mixed heights so the
# skyline is not flat, but continuous so there are no gaps to see through.
ROW = [('vernacular4', 4, 2050.0), ('deco3', 5, 2050.0), ('modern6', 4, 2050.0),
       ('vernacular7', 4, 1640.0), ('contemporary8', 5, 1640.0),
       ('deco5', 4, 2050.0), ('vernacular3', 4, 1640.0)]


def clear():
    """Remove by LABEL, via find_actors' own name filter.

    The first version matched '.HERO_' inside each actor's refPath and removed
    NOTHING while reporting success: an actor's refPath carries its internal
    NAME (Actor_23), not the label set afterwards. find_actors takes a `name`
    filter that matches the label, which is the thing we actually set.
    """
    n = 0
    for pat in ('HERO_End',):
        r = ue.tool(S, 'find_actors',
                    {'name': pat, 'tag': '', 'collision_channels': []})
        try:
            found = json.loads(r)['returnValue']
        except Exception:
            continue
        for a in found:
            ue.tool(S, 'remove_from_scene', {'actor': a})
            n += 1
    return n


def main():
    print('hero_backdrop: cleared %d' % clear())
    if '--clear' in sys.argv:
        return
    rnd = random.Random(9312)
    y = Y_FROM
    made = 0
    for i, (rid, t, w) in enumerate(ROW):
        if y > Y_TO:
            break
        asset = recipes.asset_name(rid, t, w)
        # YAW 270 so the frontage faces back down the street (-x). Verified by
        # measuring the placed actor rather than trusting the sign: this
        # project has stood a whole row on its head by guessing a rotation.
        r = ue.tool(S, 'add_to_scene_from_asset', {
            'asset_path': '%s/%s' % (BAKED, asset),
            'name': 'HERO_End%d' % i,
            'xform': {'location': {'x': END_X, 'y': y, 'z': Z},
                      'rotation': {'pitch': 0.0, 'yaw': 270.0, 'roll': 0.0},
                      'scale': {'x': 1.0, 'y': 1.0, 'z': 1.0}}})
        try:
            act = json.loads(r)['returnValue']
        except Exception:
            print('  FAILED %s: %s' % (asset, str(r)[:120]))
            y += w + 60.0
            continue
        ue.tool(A, 'set_label', {'actor': act, 'label': 'HERO_End%d' % i})
        b = json.loads(ue.tool(A, 'get_actor_bounds', {'actor': act}))['returnValue']
        made += 1
        y += (b['max']['y'] - b['min']['y']) + rnd.uniform(30.0, 140.0)
    print('hero_backdrop: %d buildings closing the vista at x=%.0f' % (made, END_X))


if __name__ == '__main__':
    main()
