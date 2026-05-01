import csv
import random
import time
from faker import Faker

TARGET_POPULATION = 1_000_000
TOTAL_GENERATIONS = 50
FAKER_POOL_SIZE = 10_000  # The size of our pre-generated name pools


def generate_family_tree():
    start_time = time.time()

    print(f"Initializing Faker and generating a pool of {FAKER_POOL_SIZE} names...")
    fake = Faker()

    # Pre-generate large pools of names to ensure huge variety without the lag of 1M Faker calls
    # Using sets inside list() ensures we only get unique names in our pools
    MALE_NAMES = list({fake.first_name_male() for _ in range(FAKER_POOL_SIZE)})
    FEMALE_NAMES = list({fake.first_name_female() for _ in range(FAKER_POOL_SIZE)})
    LAST_NAMES = list({fake.last_name() for _ in range(FAKER_POOL_SIZE)})

    print(
        f"Pool generated! (Unique Males: {len(MALE_NAMES)}, Females: {len(FEMALE_NAMES)}, Last Names: {len(LAST_NAMES)})"
    )
    print("Starting generation of 1,000,000 individuals...")

    total_individuals = 0
    current_id = 1

    # Open CSV files for writing
    with (
        open("data/individuals.csv", "w", newline="", encoding="utf-8") as f_ind,
        open("data/marriages.csv", "w", newline="", encoding="utf-8") as f_mar,
        open("data/begets.csv", "w", newline="", encoding="utf-8") as f_beg,
    ):

        ind_writer = csv.writer(f_ind)
        mar_writer = csv.writer(f_mar)
        beg_writer = csv.writer(f_beg)

        # Write Headers
        ind_writer.writerow(["ID", "First_Name", "Last_Name", "Gender", "Generation"])
        mar_writer.writerow(["Spouse1_ID", "Spouse2_ID"])
        beg_writer.writerow(["Parent_ID", "Child_ID"])

        def add_person(gen, gender=None, last_name=None):
            nonlocal current_id, total_individuals
            if total_individuals >= TARGET_POPULATION:
                return None

            if not gender:
                gender = random.choice(["M", "F"])
            first_name = (
                random.choice(MALE_NAMES)
                if gender == "M"
                else random.choice(FEMALE_NAMES)
            )
            if not last_name:
                last_name = random.choice(LAST_NAMES)

            person = (current_id, first_name, last_name, gender, gen)
            ind_writer.writerow(person)

            current_id += 1
            total_individuals += 1
            return person

        current_gen_males = []
        current_gen_females = []

        # Generation 0 baseline
        target_per_gen = TARGET_POPULATION // TOTAL_GENERATIONS
        for _ in range(target_per_gen):
            p = add_person(0)
            if p:
                if p[3] == "M":
                    current_gen_males.append(p)
                else:
                    current_gen_females.append(p)

        # Generate subsequent generations
        for gen in range(1, TOTAL_GENERATIONS):
            if total_individuals >= TARGET_POPULATION:
                break

            if gen % 10 == 0:
                print(
                    f"Processing Generation {gen}... ({total_individuals:,} individuals so far)"
                )

            next_gen_males = []
            next_gen_females = []

            # Shuffle to randomize marriages
            random.shuffle(current_gen_males)
            random.shuffle(current_gen_females)

            num_marriages = min(len(current_gen_males), len(current_gen_females))

            # Dynamically calculate required children to hit the 1M target accurately
            remaining_individuals = TARGET_POPULATION - total_individuals
            remaining_gens = TOTAL_GENERATIONS - gen
            target_this_gen = (
                remaining_individuals // remaining_gens
                if remaining_gens > 0
                else remaining_individuals
            )

            avg_children = target_this_gen / num_marriages if num_marriages > 0 else 0

            for i in range(num_marriages):
                if total_individuals >= TARGET_POPULATION:
                    break

                husband = current_gen_males[i]
                wife = current_gen_females[i]

                # Record marriage
                mar_writer.writerow([husband[0], wife[0]])

                # Add natural variance to birth rates
                base_children = int(avg_children)
                if random.random() < (avg_children - base_children):
                    num_children = base_children + 1
                else:
                    num_children = base_children

                variance = random.choice([-1, 0, 1])
                num_children = max(0, num_children + variance)

                # Generate children for this couple
                for _ in range(num_children):
                    if total_individuals >= TARGET_POPULATION:
                        break

                    child = add_person(
                        gen, last_name=husband[2]
                    )  # Child inherits father's last name
                    if child:
                        # Record both parents in the 'begets' file
                        beg_writer.writerow([husband[0], child[0]])
                        beg_writer.writerow([wife[0], child[0]])

                        if child[3] == "M":
                            next_gen_males.append(child)
                        else:
                            next_gen_females.append(child)

            current_gen_males = next_gen_males
            current_gen_females = next_gen_females

        # Pad remaining population if we fall slightly short after the final generation loop
        while total_individuals < TARGET_POPULATION:
            add_person(TOTAL_GENERATIONS - 1)

    end_time = time.time()
    print(
        f"\nDone! Generated {total_individuals:,} individuals across {TOTAL_GENERATIONS} generations."
    )
    print(f"Total Time: {end_time - start_time:.2f} seconds.")


if __name__ == "__main__":
    generate_family_tree()
