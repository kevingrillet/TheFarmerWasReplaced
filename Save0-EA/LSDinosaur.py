def runBone():
    import IBone

    ws = get_world_size()
    while num_items(Items.Bone) < 98010:
        IBone.innerfarmZZV2(ws)


runBone()

# def runBoneAggressive():
#     import UMove

#     ws = get_world_size()
#     while num_items(Items.Bone) < 98010:
#         tail = 0
#         change_hat(Hats.Dinosaur_Hat)
#         while tail < 6:
#             x, y = measure()
#             UMove.goToWarpless(x, y)
#             if get_entity_type() == Entities.Apple:
#                 tail += 1
#             else:
#                 tail = 0
#                 break

#         UMove.goToWarpless(0, 0)
#         while True:
#             for _ in range(ws-1):
#                 if not move(North):
#                     break
#             if not move(East):
#                 break
#             for _ in range(ws / 2):
#                 for _ in range(ws - 2):
#                     if not move(East):
#                         break
#                 if not move(South):
#                     break
#                 for _ in range(ws - 2):
#                     if not move(West):
#                         break
#                 if not move(South):
#                     break
#             if not move(West):
#                 break
#         change_hat(Hats.Straw_Hat)

# runBoneAggressive()
