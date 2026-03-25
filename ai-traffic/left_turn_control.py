import traci
import time
import sys
import random

# ================= SUMO CONFIG =================
sumoCmd = [
    r"C:\Program Files (x86)\Eclipse\Sumo\bin\sumo-gui.exe",
    "-c",
    r"C:\Users\NAGASHREE K S\OneDrive\Desktop\left-turn-ai\ai-traffic\sumo\config.sumocfg"
]

traci.start(sumoCmd)

print("🚀 STABLE LEFT TURN SYSTEM (NO CRASH)")
print("------------------------------------------------")

junction_id = "n1"
vehicle_id = 0


# ================= SAFE ADD VEHICLE =================
def safe_add_vehicle(route):
    global vehicle_id

    vid = f"veh{vehicle_id}"

    # 🔥 ensure ID is unique
    if vid in traci.vehicle.getIDList():
        vehicle_id += 1
        return

    try:
        traci.vehicle.add(vid, routeID=route)
        vehicle_id += 1
    except:
        pass


# ================= AUTO TRAFFIC =================
def generate_traffic():
    if random.random() < 0.5:   # 🔥 reduce load (important)
        route = random.choice([
            "left_top_to_right", "left_bottom_to_left",
            "left_left_to_top", "left_right_to_bottom",
            "straight_top_to_bottom", "straight_bottom_to_top",
            "straight_left_to_right", "straight_right_to_left",
            "right_top_to_left", "right_bottom_to_right",
            "right_left_to_bottom", "right_right_to_top"
        ])

        safe_add_vehicle(route)


# ================= MAINTAIN TRAFFIC =================
def maintain_traffic():
    current = len(traci.vehicle.getIDList())

    if current < 20:   # 🔥 controlled number
        for _ in range(5):  # 🔥 not too many at once
            route = random.choice([
                "left_top_to_right", "left_bottom_to_left",
                "left_left_to_top", "left_right_to_bottom",
                "straight_top_to_bottom", "straight_bottom_to_top",
                "straight_left_to_right", "straight_right_to_left",
                "right_top_to_left", "right_bottom_to_right",
                "right_left_to_bottom", "right_right_to_top"
            ])
            safe_add_vehicle(route)


# ================= LEFT TURN LANES =================
def get_left_turn_lanes():
    left_lanes = set()
    lanes = list(set(traci.trafficlight.getControlledLanes(junction_id)))

    for lane in lanes:
        for link in traci.lane.getLinks(lane):
            if link[6] == 'l':
                left_lanes.add(lane)

    return list(left_lanes)


# ================= LEFT TURN DATA =================
def get_left_turn_count():
    count = 0

    for lane in get_left_turn_lanes():
        vehicles = traci.lane.getLastStepVehicleIDs(lane)

        for v in vehicles:
            lane_pos = traci.vehicle.getLanePosition(v)
            lane_len = traci.lane.getLength(lane)

            if (lane_len - lane_pos) < 120:
                count += 1

    return count


# ================= CONTROL =================
def control_signal(left_count, total):
    if left_count <= 2:
        msg = f"🟢 SAFE | Total:{total} | Left:{left_count}"
        state = "GGrrGGrr"
    elif left_count <= 5:
        msg = f"🟡 MODERATE | Total:{total} | Left:{left_count}"
        state = "yyrryyrr"
    else:
        msg = f"🔴 BLOCKED | Total:{total} | Left:{left_count}"
        state = "rrGGrrGG"

    print(msg)

    try:
        traci.gui.setStatusBarText(msg)
        traci.trafficlight.setRedYellowGreenState(junction_id, state)
    except:
        pass


# ================= MAIN LOOP =================
try:
    step = 0

    while True:
        traci.simulationStep()
        time.sleep(0.08)

        generate_traffic()
        maintain_traffic()

        step += 1

        if step % 40 == 0:
            total = len(traci.vehicle.getIDList())
            left = get_left_turn_count()

            print("\n📊 STATUS")
            print(f"🚗 Total: {total}")
            print(f"⬅ Left: {left}")

            control_signal(left, total)

except Exception as e:
    print("⚠ ERROR:", e)

finally:
    print("🔴 Closing safely...")
    traci.close()
    sys.exit()