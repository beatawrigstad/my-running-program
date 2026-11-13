from dataclasses import dataclass
from drafter import *

hide_debug_information()
set_website_title("My Running Program")
set_website_framed(False)
set_site_information(author = "Beata Wrigstad",
                     description = "Generates a personalized running program based on the user's current fitness level, goal, and available time",
                     sources = ["A LLM was mainly used to brainstorm and help me improve my initial idea, as well as to review my program for potential errors and misses.", 
                                "LLM-documentation.docx"],
                     planning = ["CS1-final-project-0-BW.docx", "CS1-final-project-1-BW.docx"],
                     links = ["https://github.com/beatawrigstad/my-running-program"],
                     server=None) 

set_website_style("tacit")

@dataclass
class Runner:
    """Stores the user's running goals and current fitness level"""
    distance: float
    goal: str
    time: float
    level: int
    weeks: int
    days: int
    
@dataclass
class TrainingSession:
    """Stores information about one scheduled running session"""
    week: int
    day: str
    workout_type: str
    distance: float
    is_complete: bool
    
@dataclass
class State:
    """Stores all information needed to run the web application"""
    runner: Runner
    training_sessions: list[TrainingSession]
    current_week: int
    message: str

@route
def index(state: State) -> Page:
    """ Shows the welcome page """
    
    return Page(
        state,
        [change_color(Header("My Running Program"), "black"),
         bold("Welcome! \n"),
        "Want to take your running to the next level?",
         "\n Get a personalized running program based on your current fitness and goals! \n",
         "\n",
         Button("Let's get started", "start")
         ])

@route
def start(state: State) -> Page:
    """ A page with input fields where the user enters their level, goal and time frame. """
    
    return Page(
        state,
        [change_color(Header("Let's get started!"), "black"),
         bold("Let's start with some information about you. \n"),
         str(state.message),
         "\n What's your goal distance?",
         SelectBox("goal_distance", ["5.0", "10.0", "21.1"]), "km",
         "\n What's your main goal?",
         SelectBox("main_goal", ["Finish the distance", "Finish in a target time"]),
         "\n If your goal is to finish in a target time, what's your target finish time (in minutes)?\n",
         italic("For example, enter 25.5 for 25 minutes and 30 seconds."),
         TextBox("goal_time", " "),
         "\n What's your longest continuous run so far?",
         SelectBox("longest_run", ["I'm completely new to running", "About 5km", "More than 10km"]),
         "\n In how many weeks do you want to reach your goal?",
         SelectBox("number_of_weeks", ["4", "6", "8"]),
         "\n How many days per week do you want to run?",
         SelectBox("days_per_week", ["3", "4", "5", "6"]),
         "\n",
         Button("Enter", "enter")
         ])

@route
def enter(state: State, goal_distance: str, main_goal: str,
          goal_time: str, longest_run: str,
          number_of_weeks: str, days_per_week: str) -> Page:
    """Takes the user's input and validates them before saving their info to the state"""
    
    state.runner.distance = float(goal_distance)
    state.runner.goal = main_goal
    
    if main_goal == "Finish the distance":
        state.runner.time = 0.0
    else:
        goal_time = goal_time.strip()
        if not goal_time:
            state.message = "Please enter your target time"
            return start(state)
        elif not goal_time.replace(".", "", 1).isdigit(): # .replace(".", "", 1) removes ONE dot! 
            state.message = "Please enter your target time in minutes, for example 25.5"
            return start(state)
        elif float(goal_time) <= 0:
            state.message = "Please enter a target time greater than zero"
            return start(state)
        else:
            state.runner.time = float(goal_time)
            
    if not main_goal == "Finish the distance":
        if state.runner.distance == 5.0 and float(goal_time) < 10:
            state.message = "Please enter a realistic target time."
            return start(state)
        elif state.runner.distance == 10.0 and float(goal_time) < 20:
            state.message = "Please enter a realistic target time."
            return start(state)
        elif state.runner.distance == 21.1 and float(goal_time) < 45:
            state.message = "Please enter a realistic target time."
            return start(state)
        
    if longest_run == "I'm completely new to running":
        state.runner.level = 1
    elif longest_run == "About 5km":
        state.runner.level = 2
    else:
        state.runner.level = 3
        
    state.runner.weeks = int(number_of_weeks)
    state.runner.days = int(days_per_week)
    
    if state.runner.level == 1:
        if state.runner.distance == 10.0:
            if state.runner.weeks * state.runner.days < 16:
                state.message = "Please enter a more realistic goal."
                return start(state)
        elif state.runner.distance == 21.1:
            if state.runner.weeks * state.runner.days < 25:
                state.message = "Please enter a more realistic goal."
                return start(state)
            
    if state.runner.level == 2 and state.runner.distance == 21.1:
        if state.runner.weeks * state.runner.days < 16:
          state.message = "Please enter a more realistic goal."
              return start(state)
            
    state.current_week = 1
    state.training_sessions = []
    state.message = ""
    
    if state.runner.time > 0:
        time_message = "Your target time is " + str(state.runner.time) + " minutes."
    else:
        time_message = "Your goal is to finish the distance."

    return Page(
        state,
        [change_color(Header("Great!"), "black"),
         "You selected a " + str(state.runner.weeks) + "-week program for " + 
         str(state.runner.distance) + " km.",
         time_message, "\n",
         "\n",
         Button("Yes! Let's go!", "generate_program"),
         Button("No, I want to change the information", "change")
         ])

@route
def change(state: State) -> Page:
    """ Return to the start page where the user can edit their information"""
    state.message = ""
    return start(state)

def format_pace(pace: float) -> str:
    """Format a pace in decimal minutes to minutes and seconds per km"""
    seconds = round(pace*60)
    pace_min = seconds // 60
    pace_sec = seconds % 60
    #.zfill(2) adds 0 until the string contains two characters
    return str(pace_min) + ":" + str(pace_sec).zfill(2) + " min/km" 

def easy_run(state: State) -> tuple[str, float]:  
    """
    Calculates the length and pace of the user's easy runs
    Returns a tuple of a description of the session and the total distance
    """
    #tuple[] shows that the function returns two values as a tuple
    
    if state.runner.time == 0:
        pace = "a comfortable pace"
    else:
        target_pace = state.runner.time/state.runner.distance
        easy_pace = target_pace * 1.2
        pace = format_pace(easy_pace)
    
    if state.runner.distance == 5.0:
        if state.runner.level == 1:
            start_len = 1.5
            end_len = 3.0
        elif state.runner.level == 2:
            start_len = 3.0
            end_len = 5.0
        else:
            start_len = 4.0
            end_len = 5.0
    elif state.runner.distance == 10.0:
        if state.runner.level == 1:
            start_len = 2.5
            end_len = 5.0
        elif state.runner.level == 2:
            start_len = 4.0
            end_len = 7.0
        else:
            start_len = 5.0
            end_len = 8.5
    elif state.runner.distance == 21.1:
        if state.runner.level == 1:
            start_len = 4.0
            end_len = 8.0
        elif state.runner.level == 2:
            start_len = 5.0
            end_len = 11.0
        else:
            start_len = 8.0
            end_len = 14.0
    
    # Calculate how far the user is through the training program, 
    # which is used to gradually increase the running distance.
    progress_fraction = (state.current_week - 1) / (state.runner.weeks - 1)
    distance = start_len + (end_len - start_len) * progress_fraction
    distance = round(distance, 1) #round to one decimal 
    
    description = "Easy run: " + "\n" + str(distance) + "km @ " + pace
    
    return description, distance


def workout(state: State, workout_number: int) -> tuple[str, float]:
    """
    Generates a workout and pace based on the runner's level, goal and schedule
    Returns a tuple of a description of the session and the total distance
    """
    
    if state.runner.level == 1:
        if workout_number == 1:
            workout_type = "Run/walk"
        else:
            workout_type = "Fartlek"
    elif state.runner.level == 2:
        if workout_number == 1:
            workout_type = "Fartlek"
        else:
            workout_type = "Intervals"
    else:
        workout_type = "Intervals"
        
    if state.runner.level == 1:
        warmup = 1
        cooldown = 1
    elif state.runner.level == 2:
        if state.runner.distance == 21.1:
            warmup = 2
            cooldown = 2
        else:
            warmup = 2
            cooldown = 1
    else:
        warmup = 3
        cooldown = 2
    
    target_pace = 0.0
    if state.runner.time > 0:
        target_pace = state.runner.time / state.runner.distance
        easy_pace = format_pace(target_pace * 1.25)
        cooldown_pace = format_pace(target_pace * 1.3)
    else:
        easy_pace = "comfortable effort"
        cooldown_pace = "very comfortable effort" 
    
    progress_fraction = (state.current_week - 1) / (state.runner.weeks - 1)
    
    if workout_type == "Run/walk":
        repetitions = round(4 + 2 * progress_fraction)
        run_min = round(1 + 3 * progress_fraction)
        walk_min = round(2 - progress_fraction)
        
        if state.runner.time > 0:
            run_pace = target_pace * 1.2
        else:
            run_pace = 7.0
        
        walk_pace = 10.0
        distance = warmup + (repetitions * run_min) / run_pace + 
        (repetitions * walk_min) / walk_pace + cooldown

        description = (str(repetitions) + " x (" + str(run_min) + " min run + " +
            str(walk_min) + " min walk)")
    
    elif workout_type == "Fartlek":
        repetitions = round(4 + 2 * progress_fraction)
        hard_min = round(1 + 2 * progress_fraction)
        easy_min = 2

        if state.runner.time > 0:
            target_pace = state.runner.time / state.runner.distance
            harder_pace_value = target_pace * 0.95
            easier_pace_value = target_pace * 1.15
            harder_pace = format_pace(harder_pace_value)
            easier_pace = format_pace(easier_pace_value)
        else:
            harder_pace_value = 7.0
            easier_pace_value = 7.0
            harder_pace = "controlled hard effort"
            easier_pace = "comfortable effort"
        
        distance = warmup + repetitions * 
        (hard_min / harder_pace_value + easy_min / easier_pace_value) + cooldown

        description = (str(repetitions) + " x (" + str(hard_min) + " min hard @ " + harder_pace +
            " + " + str(easy_min) + " min easy @ " + easier_pace + ")")
        
    else:
        repetitions = round(4 + 2 * progress_fraction)

        if state.runner.distance == 5.0:
            if state.runner.level == 2:
                start_len = 500
                end_len = 700
            elif workout_number == 1:
                start_len = 600
                end_len = 1000
            else:
                start_len = 500
                end_len = 800

        elif state.runner.distance == 10.0:
            if state.runner.level == 2:
                start_len = 600
                end_len = 1000
            elif workout_number == 1:
                start_len = 800
                end_len = 1500
            else:
                start_len = 600
                end_len = 1200

        else:
            if state.runner.level == 2:
                start_len = 800
                end_len = 1200
            elif workout_number == 1:
                start_len = 1200
                end_len = 1800
            else:
                start_len = 1000
                end_len = 1600

        interval_length = round((start_len + (end_len - start_len) * progress_fraction) / 100) * 100
        rest = round(2 - 0.5 * progress_fraction, 1)
        distance = warmup + repetitions * interval_length / 1000 + cooldown

        if state.runner.time > 0:
            target_pace = state.runner.time / state.runner.distance
            if state.runner.level == 3 and workout_number == 2:
                pace_factor = 1.00 - (0.08 * progress_fraction)
                interval_pace = format_pace(target_pace * pace_factor)
            else:
                pace_factor = 1.00 - (0.05 * progress_fraction)
                interval_pace = format_pace(target_pace * pace_factor)
        else:
            interval_pace = "controlled hard effort"

        description = (str(repetitions) + " x " + str(interval_length) + "m @ " + interval_pace +
            ", " + str(rest) + " min rest")
        
    whole_workout = "Workout: " + "\n" + (str(warmup) + "km warm-up @ " + easy_pace +
                     "\n" + description + "\n" +
                     str(cooldown) + "km cool-down @ " + cooldown_pace)
        
    return whole_workout, distance
    

def long_run(state: State) -> tuple[str, float]:
    """
    Calculates the length and pace of the user's long run
    Returns a tuple of a description of the session and the total distance
    """
    
    if state.runner.time == 0:
        pace = "a comfortable pace"
    else:
        target_pace = state.runner.time/state.runner.distance
        easy_pace = target_pace * 1.25
        pace = format_pace(easy_pace)
    
    if state.runner.distance == 5.0:
        if state.runner.level == 1:
            start_len = 2.0
            end_len = 4.5
        elif state.runner.level == 2:
            start_len = 4.0
            end_len = 6.0
        else:
            start_len = 6.0
            end_len = 9.0
    elif state.runner.distance == 10.0:
        if state.runner.level == 1:
            start_len = 3.0
            end_len = 6.0
        elif state.runner.level == 2:
            start_len = 5.0
            end_len = 9.0
        else:
            start_len = 8.0
            end_len = 12.0
    elif state.runner.distance == 21.1:
        if state.runner.level == 1:
            start_len = 5.0
            end_len = 10.0
        elif state.runner.level == 2:
            start_len = 8.0
            end_len = 14.0
        else:
            start_len = 12.0
            end_len = 18.0
        
    progress_fraction = (state.current_week - 1) / (state.runner.weeks - 1)
    distance = start_len + (end_len - start_len) * progress_fraction
    distance = round(distance, 1)
    
    description = "Long run: " + "\n" + str(distance) + "km @ " + pace
    return description, distance

@route
def generate_program(state: State) -> Page:
    """ Displays the training schedule for the current week"""
    
    week_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    if state.current_week == 0:
        state.current_week = 1
    
    # Create a different weekly schedule depending on how many days per week the user wants to run
    if not state.training_sessions:
        for week in range(1, state.runner.weeks + 1):
            state.current_week = week
            
            if state.runner.days == 3:
                schedule = [easy_run(state),
                            ("Rest", 0.0),
                            workout(state, 1),
                            ("Rest", 0.0),
                            ("Rest", 0.0),
                            long_run(state),
                            ("Rest", 0.0)]
            elif state.runner.days == 4:
                schedule = [easy_run(state),
                            workout(state, 1),
                            ("Rest", 0.0),
                            easy_run(state),
                            ("Rest", 0.0),
                            long_run(state),
                            ("Rest", 0.0)]
            elif state.runner.days == 5:
                schedule = [easy_run(state),
                            workout(state, 1),
                            ("Rest", 0.0),
                            easy_run(state),
                            workout(state, 2),
                            long_run(state),
                            ("Rest", 0.0)]
            elif state.runner.days == 6:
                schedule = [easy_run(state),
                            workout(state, 1),
                            easy_run(state),
                            easy_run(state),
                            workout(state, 2),
                            long_run(state),
                            ("Rest", 0.0)]
            
            for i in range(len(schedule)):
                workout_type, distance = schedule[i]
                session = TrainingSession(week, week_days[i], workout_type, distance, False)
                state.training_sessions.append(session)
                
        state.current_week = 1
                
    current_sessions = []
    for session in state.training_sessions:
        if session.week == state.current_week:
            current_sessions.append(session)
            
    sessions = []
    for session in current_sessions:
        sessions.append(session.workout_type)
    
    explanations = []
    for session in current_sessions:
        if "Easy run" in session.workout_type:
            reason = "Keep it easy! Use the given pace as a guideline, but go by feel."
        elif "Rest" in session.workout_type:
            reason = "Prioritize recovery. Make sure to get enough fuel and sleep."
        elif "Long run" in session.workout_type:
            reason = "Time to get some extra mileage in!"
        else:
            reason = "Time to push! Challenge yourself!" 
        explanations.append(reason)
        
    buttons: list[Component | str] = [] #allows both buttons and str 
    for session in current_sessions:
        if "Rest" in session.workout_type:
            buttons.append(" ")
        elif not session.is_complete:
            buttons.append(change_background_color(Button(
                "Done!", "complete",
                {"week": session.week, "day": session.day}), "green"))
        else:
            buttons.append(change_background_color(Button(
                "Undo", "undo",
                {"week": session.week, "day": session.day}), "darkgray"))
            
    completed_sessions = []
    for session in current_sessions:
        if "Rest" in session.workout_type:
            completed_sessions.append(" ")
        elif session.is_complete:
            completed_sessions.append("✅")
        else:
            completed_sessions.append("❌")
        
    pace = "!"
    if state.runner.goal == "Finish in a target time":
        pace = " " + "in" + " " + str(state.runner.time) + "min"

    day_headers = []
    for day in week_days:
        day_headers.append(change_color(bold(day), "black"))

    explanation_cells = []
    for reason in explanations:
        explanation_cells.append(italic(reason)) 
  
    content = [
        change_color(Header("Your training schedule"), "black"),
        bold("Week: "), str(state.current_week), " of ", str(state.runner.weeks),
        Table([
          day_headers, 
          sessions, 
          explanation_cells, 
          buttons, 
          completed_sessions])
        ]
    
    if state.current_week > 1:
        content.append(Button("Previous week", "previous_week"))
    
    if state.current_week < state.runner.weeks:
        content.append(Button("Next week", "next_week"))      
    else:
        content.append("\n")
        content.append("Good job! You've reached the final week of your program! 
        After this week, you are ready to run a" + " " + str(state.runner.distance) + "km" + pace)
    content.append("\n")
    content.append("\n")
    content.append(Button("Change my information", "change"))
    content.append("\n")
    content.append(Button("View my progress", "progress"))

    return Page(state, content)

@route
def complete(state: State, week: int, day: str) -> Page:
    """Updates the given training session as complete in the state"""
    
    for session in state.training_sessions:
        if session.week == week and session.day == day:
            session.is_complete = True
    return generate_program(state)

@route
def undo(state: State, week: int, day: str) -> Page:
    """Updates the given training session as not complete in the state"""
    
    for session in state.training_sessions:
        if session.week == week and session.day == day:
            session.is_complete = False
    return generate_program(state)

@route
def previous_week(state: State) -> Page:
    """ Move back a week, if the current week is not week 1"""
    
    if state.current_week > 1:
        state.current_week -= 1
    return generate_program(state)

@route
def next_week(state: State) -> Page:
    """ Move to the next week, if it's not the last week of the program"""
    
    if state.current_week < state.runner.weeks:
        state.current_week += 1
    return generate_program(state)

@route
def progress(state: State) -> Page:
    """ Shows the user's total distance and number of sessions completed, and a message"""
    
    total_sessions = 0
    for session in state.training_sessions:
        if "Rest" not in session.workout_type:
            total_sessions += 1
    
    completed_sessions = 0
    distance = 0.0
    for session in state.training_sessions:
        if session.is_complete:
            completed_sessions += 1
            distance += session.distance
    total_distance = round(distance, 1)
    
    if state.current_week == 1:
        state.message = "It's your first week! You're doing great!"
    elif state.runner.weeks == state.current_week:
        state.message = "Congrats! You made it to your final week!"
    elif state.runner.weeks - state.current_week == 1:
        state.message = "Awesome job! Almost there!"
    elif state.current_week == state.runner.weeks // 2:
        state.message = "Halfway there, let's keep going!"
    elif len(state.training_sessions) > 0 and (completed_sessions/len(state.training_sessions)) > 0.5:
        state.message = "You're making progress! Let's keep going"
    else:
        state.message = "You're doing awesome! Let's keep it up!" 
    
    statistics = Div(
        bold("You have completed: "), str(completed_sessions), "/", 
        str(int(total_sessions)), "sessions",
        "\n", bold("Total distance: "), str(total_distance), "km",
        style_border="1px solid black",
        style_padding="10px",
        style_width="500px") 
    
    content = [
        change_color(Header("Your progress"), "black"),
        state.message,
        "\n",
        change_padding(change_border(statistics, "2px solid steelblue"), "12px"),
        "\n",
        Button("Back to schedule", "generate_program")
        ]
    return Page(state, content)
    
start_server(State(Runner(0.0, "", 0.0, 0, 0, 0), [], 1, ""))
