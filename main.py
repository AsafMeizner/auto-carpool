import csv
from tkinter import Tk, Toplevel, Label, Button, Entry, Checkbutton, IntVar, StringVar, Listbox, SINGLE, messagebox
from collections import defaultdict
import numpy as np

class CarpoolManager:
    def __init__(self, master):
        self.master = master
        self.master.title("Carpool Manager")

        # Load data from CSVs
        self.areas = self.load_csv("people_areas.csv")
        self.people = {person for area in self.areas.values() for person in area}
        self.selected_people = {}  # Holds checkboxes for people present today
        self.drivers = {}          # Holds information about drivers
        self.extra_people = set()  # Temporary people added for this session
        self.distance_matrix = self.load_distance_matrix("distance_matrix.csv")  # Load the distance matrix

        # Print areas and residents for debugging
        print("Areas and Residents:")
        for area, residents in self.areas.items():
            print(f"{area}: {', '.join(residents)}")

        # UI elements for selecting present people
        Label(master, text="Select people present today:").grid(row=0, column=0, sticky="w")
        self.create_people_checkboxes()

        Button(master, text="Add Student", command=self.add_student).grid(row=10, column=0, pady=5)
        Button(master, text="Next", command=self.open_driver_assignment).grid(row=11, column=0, pady=10)

    def load_csv(self, filename):
        areas = defaultdict(list)
        try:
            with open(filename, "r") as csvfile:
                reader = csv.reader(csvfile)
                for row in reader:
                    area = row[0]
                    people = row[1:]
                    areas[area].extend(person.strip() for person in people if person.strip())
        except FileNotFoundError:
            messagebox.showerror("Error", f"CSV file '{filename}' not found.")
        return areas

    def load_distance_matrix(self, filename):
        distance_matrix = {}
        try:
            with open(filename, "r") as csvfile:
                reader = csv.reader(csvfile)
                areas = next(reader)[1:]  # First row contains area names
                for row in reader:
                    origin = row[0]
                    distances = list(map(float, row[1:]))
                    distance_matrix[origin] = dict(zip(areas, distances))
        except FileNotFoundError:
            messagebox.showerror("Error", f"CSV file '{filename}' not found.")
        return distance_matrix

    def create_people_checkboxes(self):
        row = 1
        for person in sorted(self.people):
            var = IntVar()
            Checkbutton(self.master, text=person, variable=var).grid(row=row, column=0, sticky="w")
            self.selected_people[person] = var
            row += 1

    def add_student(self):
        def save_student():
            name = name_var.get().strip()
            area = area_var.get().strip()
            if name and area:
                self.areas[area].append(name)
                self.people.add(name)
                self.extra_people.add(name)
                var = IntVar()
                Checkbutton(self.master, text=name, variable=var).grid(row=len(self.selected_people) + 1, column=0, sticky="w")
                self.selected_people[name] = var
                add_window.destroy()
            else:
                messagebox.showerror("Error", "Both name and area must be provided.")

        add_window = Toplevel(self.master)
        add_window.title("Add Student")

        Label(add_window, text="Student Name:").grid(row=0, column=0, sticky="w")
        name_var = StringVar()
        Entry(add_window, textvariable=name_var).grid(row=0, column=1, sticky="w")

        Label(add_window, text="Area:").grid(row=1, column=0, sticky="w")
        area_var = StringVar()
        Entry(add_window, textvariable=area_var).grid(row=1, column=1, sticky="w")

        Button(add_window, text="Save", command=save_student).grid(row=2, column=0, columnspan=2, pady=5)

    def open_driver_assignment(self):
        present_people = [person for person, var in self.selected_people.items() if var.get() == 1]
        if not present_people:
            messagebox.showerror("Error", "Please select at least one person present today.")
            return

        self.driver_window = Toplevel(self.master)
        self.driver_window.title("Driver Assignment")

        Label(self.driver_window, text="Assign drivers:").grid(row=0, column=0, sticky="w")

        self.driver_listbox = Listbox(self.driver_window, selectmode=SINGLE)
        for person in sorted(self.people):
            self.driver_listbox.insert("end", person)
        self.driver_listbox.grid(row=1, column=0, sticky="w")

        Label(self.driver_window, text="Number of seats (excluding driver):").grid(row=2, column=0, sticky="w")
        self.seats_var = StringVar()
        Entry(self.driver_window, textvariable=self.seats_var).grid(row=3, column=0, sticky="w")

        self.driver_type = IntVar()
        Checkbutton(self.driver_window, text="Parent Driving", variable=self.driver_type).grid(row=4, column=0, sticky="w")

        Button(self.driver_window, text="Add Driver", command=self.add_driver).grid(row=5, column=0, pady=5)
        Button(self.driver_window, text="Finalize", command=self.finalize_drivers).grid(row=6, column=0, pady=5)

        self.driver_display = Listbox(self.driver_window, selectmode=SINGLE)
        self.driver_display.grid(row=7, column=0, sticky="w")

    def add_driver(self):
        selected = self.driver_listbox.curselection()
        if not selected:
            messagebox.showerror("Error", "Please select a driver.")
            return

        driver = self.driver_listbox.get(selected)
        try:
            seats = int(self.seats_var.get())
            if seats < 0:
                raise ValueError("Number of seats cannot be negative.")
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number of seats.")
            return

        self.drivers[driver] = (seats, bool(self.driver_type.get()))
        self.driver_display.insert("end", f"{driver}: {seats} seats (Parent Driving: {'Yes' if self.driver_type.get() else 'No'})")
        self.seats_var.set("")

    def finalize_drivers(self):
        if not self.drivers:
            messagebox.showerror("Error", "Please add at least one driver.")
            return

        self.assign_rides()

    def assign_rides(self):
        remaining_people = {person for person, var in self.selected_people.items() if var.get() == 1}
        ride_assignments = defaultdict(list)
        distance_travelled = defaultdict(float)

        # Start each drive from "Tichonet"
        start_area = "Tichonet"
        
        # Sort drivers and assign rides
        for driver, (seats, is_parent) in self.drivers.items():
            if is_parent:
                # Parent driving means they take their child first
                child = next((p for p in self.areas.get(driver, []) if p in remaining_people), None)
                if child:
                    ride_assignments[driver].append(child)
                    remaining_people.remove(child)
                    distance_travelled[driver] += self.distance_matrix[start_area][driver]
            
            elif driver in remaining_people:
                # Driver is also a person needing a ride, so we remove them from remaining people
                remaining_people.remove(driver)

            # Now assign seats for this driver if there are any left
            for _ in range(seats):
                if not remaining_people:
                    break  # No more people to assign
                
                # Calculate the distances from the current location and select the closest person
                best_person = None
                min_distance = float('inf')
                for person in remaining_people:
                    for area in self.areas:
                        if person in self.areas[area]:
                            distance = self.distance_matrix[start_area][area]  # Distance from Tichonet to the person's area
                            if distance < min_distance:
                                best_person = person
                                min_distance = distance
                if best_person:
                    ride_assignments[driver].append(best_person)
                    remaining_people.remove(best_person)
                    distance_travelled[driver] += min_distance  # Add the distance for this assignment

        # Display the assignments in a new window
        assignment_window = Toplevel(self.master)
        assignment_window.title("Ride Assignments")

        for driver, passengers in ride_assignments.items():
            Label(assignment_window, text=f"Driver: {driver}").pack(anchor="w")
            for passenger in passengers:
                Label(assignment_window, text=f"- {passenger}").pack(anchor="w")
            Label(assignment_window, text="").pack()  # Spacer

        if remaining_people:
            Label(assignment_window, text="Unassigned people:").pack(anchor="w")
            for person in remaining_people:
                Label(assignment_window, text=f"- {person}").pack(anchor="w")

if __name__ == "__main__":
    root = Tk()
    app = CarpoolManager(root)
    root.mainloop()
