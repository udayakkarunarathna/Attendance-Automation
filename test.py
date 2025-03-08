import numpy as np
import matplotlib.pyplot as plt

# Define the cost function for the roads
def road_cost(x, capacity=100, base_cost=1):
    """The cost of using a road is quadratic, depending on the number of cars."""
    return base_cost + (x / capacity) ** 2

# Total number of cars
total_cars = 10

# Function to compute the total cost for a given distribution of cars on two roads
def total_cost(road1_cars, road2_cars):
    cost1 = road_cost(road1_cars)
    cost2 = road_cost(road2_cars)
    return road1_cars * cost1 + road2_cars * cost2

# Find the social optimum (minimal total cost)
def social_optimum(total_cars, capacity=100):
    min_cost = float('inf')
    best_split = None
    # Try all splits of the total cars between the two roads
    for road1_cars in range(total_cars + 1):
        road2_cars = total_cars - road1_cars
        cost = total_cost(road1_cars, road2_cars)
        if cost < min_cost:
            min_cost = cost
            best_split = (road1_cars, road2_cars)
    return min_cost, best_split

# Nash equilibrium: self-interested behavior
def nash_equilibrium(total_cars, capacity=100):
    # Each driver tries to minimize their cost by choosing the road
    road1_cars = total_cars // 2
    road2_cars = total_cars - road1_cars
    
    # Simulate the process where each road gets cars until their cost is the same
    while road1_cars > 0 and road2_cars < total_cars:
        if road_cost(road1_cars) < road_cost(road2_cars):
            road1_cars -= 1
            road2_cars += 1
        else:
            break
    return total_cost(road1_cars, road2_cars)

# Compute PoA
social_cost, _ = social_optimum(total_cars)
nash_cost = nash_equilibrium(total_cars)

PoA = nash_cost / social_cost
print(f"Price of Anarchy: {PoA:.2f}")

# Plotting the results
road1_cars = np.arange(total_cars + 1)
road2_cars = total_cars - road1_cars
costs = [total_cost(r1, r2) for r1, r2 in zip(road1_cars, road2_cars)]

plt.plot(road1_cars, costs, label='Total Cost (Selfish Behavior)', color='red')
plt.axvline(x=total_cars // 2, linestyle='--', color='green', label='Nash Equilibrium')
plt.title("Price of Anarchy in Traffic Flow")
plt.xlabel("Cars on Road 1")
plt.ylabel("Total Cost")
plt.legend()
plt.show()
