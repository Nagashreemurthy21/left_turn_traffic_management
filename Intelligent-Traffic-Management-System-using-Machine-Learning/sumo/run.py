import traci

# Start SUMO
sumoCmd = ["sumo-gui", "-c", "config.sumocfg"]
traci.start(sumoCmd)

junction_id = "center"

while traci.simulation.getMinExpectedNumber() > 0:
    traci.simulationStep()

    # Get all lanes controlled by traffic light
    lanes = traci.trafficlight.getControlledLanes(junction_id)

    lane_counts = {}

    # Count vehicles in each lane
    for lane in lanes:
        lane_counts[lane] = traci.lane.getLastStepVehicleNumber(lane)

    print("Lane counts:", lane_counts)

    # -------- LEFT TURN PRIORITY LOGIC --------
    left_turn_lanes = [lane for lane in lanes if "left" in lane]

    left_count = sum(traci.lane.getLastStepVehicleNumber(l) for l in left_turn_lanes)

    if left_count > 2:
        print("Giving priority to LEFT TURN")
        traci.trafficlight.setPhase(junction_id, 2)

    else:
        # Normal logic: max traffic lane gets priority
        max_lane = max(lane_counts, key=lane_counts.get)

        if "north" in max_lane:
            traci.trafficlight.setPhase(junction_id, 0)
        elif "south" in max_lane:
            traci.trafficlight.setPhase(junction_id, 1)
        elif "east" in max_lane:
            traci.trafficlight.setPhase(junction_id, 3)
        elif "west" in max_lane:
            traci.trafficlight.setPhase(junction_id, 4)

traci.close()