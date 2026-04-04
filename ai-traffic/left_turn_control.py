import traci
import time
import sys
import random
import winsound

# ================= SUMO CONFIG =================
sumoCmd = [
    r"C:\Program Files (x86)\Eclipse\Sumo\bin\sumo-gui.exe",
    "-c",
    r"C:\Users\NAGASHREE K S\OneDrive\Desktop\left-turn-ai\ai-traffic\sumo\config.sumocfg"
]

traci.start(sumoCmd)

print("🚀 SMART TRAFFIC SYSTEM (CLEAR LANES + PEDESTRIANS)")
print("------------------------------------------------")

junction_id = "n1"
vehicle_id = 0
ped_id = 0

# 🔊 ================= BEEP CONTROL =================
last_beep_time = 0

def play_beep():
    global last_beep_time
    if time.time() - last_beep_time > 3:   # ⛔ avoid spam
        for _ in range(3):
            winsound.Beep(1200, 300)
        last_beep_time = time.time()


# ================= CROSSWALK EDGES =================
CROSSWALK_EDGES = {
    "TOP": ["top_in", "top_out"],
    "BOTTOM": ["bottom_in", "bottom_out"],
    "LEFT": ["left_in", "left_out"],
    "RIGHT": ["right_in", "right_out"]
}


# ================= SAFE ADD VEHICLE =================
def safe_add_vehicle(route):
    global vehicle_id
    vid = f"veh{vehicle_id}"

    if vid in traci.vehicle.getIDList():
        vehicle_id += 1
        return

    try:
        traci.vehicle.add(vid, routeID=route)
        vehicle_id += 1
    except:
        pass


# ================= SAFE ADD PEDESTRIAN =================
def safe_add_pedestrian():
    global ped_id
    pid = f"ped{ped_id}"

    try:
        edges = traci.edge.getIDList()

        if len(edges) < 2:
            return

        start = random.choice(edges)
        end = random.choice(edges)

        if start != end:
            traci.person.add(pid, start, pos=0)
            traci.person.appendWalkingStage(pid, [end], duration=40)
            traci.person.setColor(pid, (255, 255, 0))
            ped_id += 1
    except:
        pass


# ================= GENERATE TRAFFIC =================
def generate_traffic():
    if random.random() < 0.5:
        route = random.choice([
            "left_top_to_right", "left_bottom_to_left",
            "left_left_to_top", "left_right_to_bottom",
            "straight_top_to_bottom", "straight_bottom_to_top",
            "straight_left_to_right", "straight_right_to_left",
            "right_top_to_left", "right_bottom_to_right",
            "right_left_to_bottom", "right_right_to_top"
        ])
        safe_add_vehicle(route)


# ================= GENERATE PEDESTRIANS =================
def generate_pedestrians():
    if random.random() < 0.3:
        safe_add_pedestrian()


# ================= MAINTAIN TRAFFIC =================
def maintain_traffic():
    if len(traci.vehicle.getIDList()) < 25:
        for _ in range(3):
            generate_traffic()

    if len(traci.person.getIDList()) < 12:
        for _ in range(2):
            generate_pedestrians()


# ================= LANE CLASSIFICATION =================
def get_lane_types():
    left, straight, right = set(), set(), set()
    lanes = list(set(traci.trafficlight.getControlledLanes(junction_id)))

    for lane in lanes:
        for link in traci.lane.getLinks(lane):
            direction = link[6]

            if direction == 'l':
                left.add(lane)
            elif direction == 's':
                straight.add(lane)
            elif direction == 'r':
                right.add(lane)

    return list(left), list(straight), list(right)


# ================= COUNT VEHICLES =================
def count_by_lane_type():
    left_lanes, straight_lanes, right_lanes = get_lane_types()

    def count(lanes, color):
        c = 0
        for lane in lanes:
            vehicles = traci.lane.getLastStepVehicleIDs(lane)

            for v in vehicles:
                try:
                    lane_pos = traci.vehicle.getLanePosition(v)
                    lane_len = traci.lane.getLength(lane)

                    if (lane_len - lane_pos) < 120:
                        traci.vehicle.setColor(v, color)
                        c += 1
                except:
                    pass
        return c

    left_count = count(left_lanes, (255, 0, 0))
    straight_count = count(straight_lanes, (0, 255, 0))
    right_count = count(right_lanes, (0, 0, 255))

    return left_count, straight_count, right_count


# ================= PEDESTRIAN ZONES =================
def get_pedestrian_zones():
    zone_count = {"TOP": 0, "BOTTOM": 0, "LEFT": 0, "RIGHT": 0}

    for pid in traci.person.getIDList():
        try:
            edge = traci.person.getRoadID(pid)

            for zone, edges in CROSSWALK_EDGES.items():
                if edge in edges:
                    zone_count[zone] += 1
        except:
            pass

    return zone_count


# ================= SIGNAL CONTROL =================
def control_signal():
    left, straight, right = count_by_lane_type()
    ped_zones = get_pedestrian_zones()
    total = len(traci.vehicle.getIDList())

    print("\n📊 TRAFFIC STATUS")
    print(f"🚗 Total Vehicles: {total}")
    print(f"⬅ Left: {left} | ⬆ Straight: {straight} | ➡ Right: {right}")

    print("🚶 Pedestrian Zones:")
    for z, c in ped_zones.items():
        if c > 0:
            print(f"   {z}: {c}")

    # ================= DECISION =================
    total_ped = sum(ped_zones.values())

    if True:
        msg = "🚶 PEDESTRIAN CROSSING ACTIVE"
        state = "rrrrrrrr"

        print("🚶 WALK SIGNAL ON")
        play_beep()

        # ⏱ COUNTDOWN
        for i in range(5, 0, -1):
            print(f"⏱ Crossing ends in {i} sec")
            time.sleep(1)

    elif left <= 2:
        msg = "🟢 LEFT TURN SAFE"
        state = "GGrrGGrr"

    elif left <= 5:
        msg = "🟡 LEFT TURN MODERATE"
        state = "yyrryyrr"

    else:
        msg = "🔴 LEFT TURN BLOCKED"
        state = "rrGGrrGG"

    print(f"\n🚦 {msg}")

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
        generate_pedestrians()
        maintain_traffic()

        step += 1

        if step % 40 == 0:
            control_signal()

except Exception as e:
    print("⚠ ERROR:", e)

finally:
    print("🔴 Closing safely...")
    traci.close()
    sys.exit()