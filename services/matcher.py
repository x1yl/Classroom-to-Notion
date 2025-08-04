import json
from typing import List, Dict, Any


class NotionAssignmentMatcher:
    def __init__(self, activities: List[Any], output_path: str):
        self.activities = activities
        self.output_path = output_path

    def assign_teachers(self) -> None:
        print("Assign teachers to activities:")
        for i, activity in enumerate(self.activities):
            if isinstance(activity, dict) and "title" in activity:
                teacher = input(
                    f"Enter teacher name for '{activity['title']}' (or press Enter to skip): "
                )
                activity["teacher"] = teacher.strip()
            elif isinstance(activity, str):
                print(f"Warning: Activity {i} is a string: '{activity}'. Skipping.")
            else:
                print(f"Warning: Activity {i} is not in the expected format. Skipping.")
                print(f"Activity data: {activity}")

    def save_activities(self) -> None:
        with open(self.output_path, "w") as file:
            json.dump(self.activities, file, indent=2)
        print(f"Activities with teachers saved to {self.output_path}")

    def match_assignment_to_activity(self, assignment: Dict) -> str:
        posted_by = assignment.get("posted_by", "").lower()
        for activity in self.activities:
            if isinstance(activity, dict) and "teacher" in activity:
                if activity["teacher"].lower() in posted_by:
                    return activity.get("id", "")
        return ""

    def run(self) -> None:
        if not self.activities:
            print("No activities provided.")
            return

        print("Debug: First few activities:")
        for i, activity in enumerate(self.activities):
            print(f"Activity {i}: {type(activity)} - {activity}")

        self.assign_teachers()
        self.save_activities()

        print(
            "\nMatching system ready. You can now use this to match assignments to activities."
        )

    def get_activities(self) -> List[Any]:
        return self.activities
