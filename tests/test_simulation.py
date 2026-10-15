from sphero_vicon_swarm.simulation import default_three_robot_simulation


def test_simulated_robot_moves_after_breakaway_command() -> None:
    robot = default_three_robot_simulation()[0]
    x0, y0 = robot.x_mm, robot.y_mm
    robot.command(0, 180)
    for _ in range(100):
        robot.step(0.02)
    assert abs(robot.x_mm - x0) + abs(robot.y_mm - y0) > 10
