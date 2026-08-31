"""Re-fit the backdrop and ground to the board.

The board grew north to Y 4510 for the works and the backdrop stayed where it
was, so it now cuts through the view as a grey plane. It is a stage element -
it should follow the board, not be authored once and left.
"""
import unreal, _path
import citygeom as G
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
x0, y0, x1, y1 = G.board_rect()
cx, cy = (x0 + x1)/2.0, (y0 + y1)/2.0
W, D = x1 - x0, y1 - y0
done = []
for a in eas.get_all_level_actors():
    l = a.get_actor_label()
    if l == 'STAGE_Backdrop':
        # stand it well clear of the board's far corner and make it big enough
        a.set_actor_location(unreal.Vector(cx, y1 + D*0.22, 0.0), False, False)
        a.set_actor_scale3d(unreal.Vector(max(W, D)*0.020, 1.0, max(W, D)*0.010))
        done.append(l)
    elif l == 'STAGE_Ground':
        a.set_actor_location(unreal.Vector(cx, cy, -14.0), False, False)
        # 0.045 made the floor 4.5x the board - 51,000 uu of ground the rect
        # lights cannot reach, so the board read as a bright island in a void
        # at mean 60. 1.5x is a room, not a plain.
        a.set_actor_scale3d(unreal.Vector(W*0.015, D*0.015, 1.0))
        done.append(l)
print('re-fitted: %s   board %.0f x %.0f' % (', '.join(done) or 'nothing', W, D))
les.save_current_level()
