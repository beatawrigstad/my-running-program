from dataclasses import dataclass
from drafter import *
from bakery import assert_equal

hide_debug_information()
set_website_title("My Running Program")
set_website_framed(False)
set_site_information(author = "Beata Wrigstad",
                     description = "Generates a personalized running program based on the user's current fitness level, goal, and available time",
                     sources = ["A LLM was mainly used to brainstorm and help me improve my initial idea, as well as to review my program for potential errors and misses.", 
                                "LLM-documentation.docx"],
                     planning = ["CS1-final-project-0-BW.docx", "CS1-final-project-1-BW.docx", "CS1-template-BW.pdf"],
                     links = ["https://github.com/beatawrigstad/my-running-program"],
                     server=None) 

set_website_style("tacit")

# DATACLASSES

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
    """Stores information about the runner, their training sessions, the current week, and a message to the user"""
    runner: Runner
    training_sessions: list[TrainingSession]
    current_week: int
    message: str

# CONSTANTS

WEEK_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday",
    "Friday", "Saturday", "Sunday"]

REST_SESSION = ("Rest", 0.0)

# HELPER FUNCTIONS

def validate_goal_time(goal_time: str) -> bool:
    """
    Evaluates whether the user's input time is valid 
    Arg:
        goal_time[str]: the time entered in the input field for goal time
    Returns:
        bool: True if the goal time is a positive number
    """
    goal_time = goal_time.strip()
    if not goal_time:
        return False
    if not goal_time.replace(".", "", 1).isdigit():
        return False
    return float(goal_time) > 0

def validate_realistic_time(distance: float, time: float) -> bool:
    """
    Checks whether the target time is realistic for the selected distance
    Arg:
        distance[float]: the distance selected in the selectbox for goal distance
        time[float]: time enetered in the input field for goal time
    Returns:
        bool: True if the time os realistic for the distance.
    """

    if distance == 5.0 and time < 10:
        return False
    elif distance == 10.0 and time < 20:
        return False
    elif distance == 21.1 and time < 45:
        return False
    return True

def get_runner_level(longest_run: str) -> int:
    """
    Returns the runner's level based on their longest continuous run
    Arg:
        longest_run[str]: the string selected for the user's longest continous run
    Returns:
        int: number represting the users level
    """
    if longest_run == "I'm completely new to running":
        return 1
    elif longest_run == "About 5km":
        return 2
    else:
        return 3

def validate_training_goal(distance: float, level: int,weeks: int, days: int) -> bool:
    """
    Checks whether the training timeframe is sufficient
    Arg:
        distance[float]: the user's goal distance
        level[int]: the user's current fitness level
        weeks[int]: the number of weeks the user want to reach their goal in
        days[int]: the number of days per week the user want to run
    Returns:
        bool: True if their goal is realistic within their timeframe
    """

    total_training_days = weeks * days
    if level == 1:
        if distance == 10.0 and total_training_days < 16:
            return False
        elif distance == 21.1 and total_training_days < 25:
            return False
    if level == 2 and distance == 21.1:
        if total_training_days < 16:
            return False
    return True

def get_time_message(runner: Runner) -> str:
    """
    Returns a message describing the runner's goal
    Arg:
        runner[Runner]: describes the user's current fitness level, goal, and timeframe.
    Returns:
        str: message reflecting their inputs
    """
    if runner.time > 0:
        return "Your target time is " + str(runner.time) + " minutes."
    return "Your goal is to finish the distance."

def format_pace(pace: float) -> str:
    """
    Format a pace in decimal minutes to minutes and seconds per km

    Arg:
      pace[float]: a pace in decmial minutes 
    Returns:
      str: the pace in minutes:seconds (min/km)
    """
    seconds = round(pace*60)
    pace_min = seconds // 60
    pace_sec = seconds % 60

    #.zfill(2) adds 0 until the string contains two characters
    return str(pace_min) + ":" + str(pace_sec).zfill(2) + " min/km" 

def get_easy_run_distances(state: State) -> tuple[float, float]:
    """
    Returns the starting and ending distances for easy runs
    Arg:
        state[State]: the current state
    Returns:
        tuple: floats representing initial and final distance of easy runs of the program
    """
    distance = state.runner.distance
    level = state.runner.level

    if distance == 5.0:
        if level == 1:
            return 1.5, 3.0
        elif level == 2:
            return 3.0, 5.0
        else:
            return 4.0, 5.0
    elif distance == 10.0:
        if level == 1:
            return 2.5, 5.0
        elif level == 2:
            return 4.0, 7.0
        else:
            return 5.0, 8.5
    else:
        if level == 1:
            return 4.0, 8.0
        elif level == 2:
            return 5.0, 11.0
        else:
            return 8.0, 14.0

def easy_run(state: State) -> tuple[str, float]: #tuple[] shows that the function returns two values as a tuple 
    """
    Calculates the length and pace of the user's easy runs
    
    Arg:
      state[State]: the current state
    Returns:
      tuple: a tuple of a description of the session (str) and the total distance (float)
    """
    
    if state.runner.time == 0:
        pace = "a comfortable pace"
    else:
        target_pace = state.runner.time/state.runner.distance
        easy_pace = target_pace * 1.2
        pace = format_pace(easy_pace)
    
    start_len, end_len = get_easy_run_distances(state)
    
    # Calculate how far the user is through the training program, which is used to gradually increase the running distance.
    progress_fraction = (state.current_week - 1) / (state.runner.weeks - 1)
    
    distance = start_len + (end_len - start_len) * progress_fraction
    distance = round(distance, 1) #round to one decimal 
    
    description = "Easy run: " + "\n" + str(distance) + "km @ " + pace
    
    return description, distance

def get_workout_type(state: State, workout_number: int) -> str:
    """
    Selects the workout type based on the runner's level
    Arg:
        state[State]: the current state
        workout_number: the number of workour of the week
    Returns:
        str: name of the appropriate workout 
    """
    if state.runner.level == 1:
        if workout_number == 1:
            return "Run/walk"
        return "Fartlek"
    elif state.runner.level == 2:
        if workout_number == 1:
            return "Fartlek"
        return "Intervals"
    return "Intervals"

def get_warmup_cooldown(state: State) -> tuple[int, int]:
    """
    Returns the warm-up and cool-down distances
    Arg:
        state[State]: the current state
    Returns:
        tuple: integers represeting warmup, cooldown
    """
    if state.runner.level == 1:
        return 1, 1
    elif state.runner.level == 2:
        if state.runner.distance == 21.1:
            return 2, 2
        return 2, 1
    return 3, 2

def get_interval_distances(state: State,
                           workout_number: int) -> tuple[int, int]:
    """
    Caculates the starting and ending interval distances in meters
    Arg:
        state[State]: the current state
        workout_number: the number of workout of the week
    Returns:
        tuple: integers represeting the initial and final distances of the intervals of the program
    """
    distance = state.runner.distance
    level = state.runner.level

    if distance == 5.0:
        if level == 2:
            return 500, 700
        elif workout_number == 1:
            return 600, 1000
        else:
            return 500, 800
    elif distance == 10.0:
        if level == 2:
            return 600, 1000
        elif workout_number == 1:
            return 800, 1500
        else:
            return 600, 1200
    else:
        if level == 2:
            return 800, 1200
        elif workout_number == 1:
            return 1200, 1800
        else:
            return 1000, 1600

def workout(state: State, workout_number: int) -> tuple[str, float]:
    """
    Generates a workout and pace based on the runner's level, goal and schedule
    
    Arg:
      state[State]: the current state
      workout_number[int]: the number of workout of the week 
    Returns:
      tuple: a tuple of a description of the session (str) and the total distance (float)
    """
  
    workout_type = get_workout_type(state, workout_number) 
    warmup, cooldown = get_warmup_cooldown(state)
    
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
        distance = warmup + (repetitions * run_min) / run_pace + (repetitions * walk_min) / walk_pace + cooldown

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
        
        distance = warmup + repetitions * (hard_min / harder_pace_value + easy_min / easier_pace_value) + cooldown

        description = (str(repetitions) + " x (" + str(hard_min) + " min hard @ " + harder_pace +
            " + " + str(easy_min) + " min easy @ " + easier_pace + ")")
        
    else:
        repetitions = round(4 + 2 * progress_fraction)

        start_len, end_len = get_interval_distances(state, workout_number)

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
    
def get_long_run_distances(state: State) -> tuple[float, float]:
    """
    Calculates the starting and ending distances for long runs
    Arg:
        state[State]: the current state
    Returns:
        tuple: floats representing the initial and final distances of long runs of the program
    """
    distance = state.runner.distance
    level = state.runner.level

    if distance == 5.0:
        if level == 1:
            return 2.0, 4.5
        elif level == 2:
            return 4.0, 6.0
        else:
            return 6.0, 9.0
    elif distance == 10.0:
        if level == 1:
            return 3.0, 6.0
        elif level == 2:
            return 5.0, 9.0
        else:
            return 8.0, 12.0
    else:
        if level == 1:
            return 5.0, 10.0
        elif level == 2:
            return 8.0, 14.0
        else:
            return 12.0, 18.0
          
def long_run(state: State) -> tuple[str, float]:
    """
    Calculates the length and pace of the user's long run
    
    Arg:
      state[State]: the current state
    Returns:
      tuple: a tuple of a description of the session (str) and the total distance (float)
    """
    
    if state.runner.time == 0:
        pace = "a comfortable pace"
    else:
        target_pace = state.runner.time/state.runner.distance
        easy_pace = target_pace * 1.25
        pace = format_pace(easy_pace)
    
    start_len, end_len = get_long_run_distances(state)
        
    progress_fraction = (state.current_week - 1) / (state.runner.weeks - 1)
    distance = start_len + (end_len - start_len) * progress_fraction
    distance = round(distance, 1)
    
    description = "Long run: " + "\n" + str(distance) + "km @ " + pace
    return description, distance

def get_weekly_schedule(state: State) -> list:
    """
    Creates a weekly schedule based on the number of running days
    Arg:
        state[State]: the current state
    Returns:
        list: the user's weekly training schedule
    """
    if state.runner.days == 3:
        return [
            easy_run(state),
            REST_SESSION,
            workout(state, 1),
            REST_SESSION,
            REST_SESSION,
            long_run(state),
            REST_SESSION
        ]
    elif state.runner.days == 4:
        return [
            easy_run(state),
            workout(state, 1),
            REST_SESSION,
            easy_run(state),
            REST_SESSION,
            long_run(state),
            REST_SESSION
        ]
    elif state.runner.days == 5:
        return [
            easy_run(state),
            workout(state, 1),
            REST_SESSION,
            easy_run(state),
            workout(state, 2),
            long_run(state),
            REST_SESSION
        ]
    else:
        return [
            easy_run(state),
            workout(state, 1),
            easy_run(state),
            easy_run(state),
            workout(state, 2),
            long_run(state),
            REST_SESSION
        ]
      
@route
def index(state: State) -> Page:
    """ 
    Shows the welcome page 

    Arg: 
      state[State]: the current state
    Returns:
      Page: page showing the welcome page
    """
    
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
    """ 
    A page with input fields where the user enter their information
    
    Arg: 
      state[State]: the current state
    Returns:
      Page: Page with input fields where the user enters their level, goal and time frame
    """
    
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
    """
    Takes the user's input and validates them before saving their info to the state
    
    Arg: 
      state[State]: the current state
      goal_distance[str]: the user's goal distance entered in the input fields
      main_goal[str]: the user's main goal entered in the input fields
      goal_time[str]: the user's goal time (if any) entered in the input fields
      longest_run[str]: the user's longest continous run so far, entered in the input fields
      number_of_weeks[str]: in how many weeks the user want to reach their goal, entered in the input fields
      days_per_week[str]: how many days per week the user wants to run, entered in the input fields
    Returns:
      Page: Page where the user confirm their information
    """
    distance = float(goal_distance)
    level = get_runner_level(longest_run)
    weeks = int(number_of_weeks)
    days = int(days_per_week)

    if main_goal == "Finish the distance":
        time = 0.0
    else:
        if not validate_goal_time(goal_time):
            state.message = "Please enter a valid target time greater than zero, for example 25.5"
            return start(state)
        time = float(goal_time)
        if not validate_realistic_time(distance, time):
            state.message = "Please enter a realistic target time."
            return start(state)
    if not validate_training_goal(distance, level, weeks, days):
        state.message = "Please enter a more realistic goal."
        return start(state)

    state.runner.distance = distance
    state.runner.goal = main_goal
    state.runner.time = time
    state.runner.level = level
    state.runner.weeks = weeks
    state.runner.days = days

    state.current_week = 1
    state.training_sessions = []
    state.message = ""

    return Page(
        state,
        [change_color(Header("Great!"), "black"),
         "You selected a " + str(state.runner.weeks) +
         "-week program for " + str(state.runner.distance) + " km.",
         get_time_message(state.runner),
         "\n",
         "\n",
         Button("Yes! Let's go!", "generate_program"),
         Button("No, I want to change the information", "change")
         ])

@route
def change(state: State) -> Page:
    """ 
    Return to the start page where the user can edit their information
    
    Arg:
      state[State]: the current state
    Returns:
      Page: the start Page  
    """
    state.message = ""
    return start(state)


@route
def generate_program(state: State) -> Page:
    """ 
    Displays the training schedule for the current week

    Arg:
      state[State]: the current state
    Returns:
      Page: a page displaying the user's training program for the current week
    """
    if state.current_week == 0:
        state.current_week = 1
    
    # Create a different weekly schedule depending on how many days per week the user wants to run
    if not state.training_sessions:
        for week in range(1, state.runner.weeks + 1):
            state.current_week = week

            schedule = get_weekly_schedule(state)
            
            for i in range(len(schedule)):
                workout_type, distance = schedule[i]
                session = TrainingSession(week, WEEK_DAYS[i], workout_type, distance, False)
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
        
    buttons = [] 
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
    for day in WEEK_DAYS:
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
        content.append("Good job! You've reached the final week of your program! After this week, you are ready to run a" +
                       " " + str(state.runner.distance) + "km" + pace)
    content.append("\n")
    content.append("\n")
    content.append(Button("Change my information", "change"))
    content.append("\n")
    content.append(Button("View my progress", "progress"))

    return Page(state, content)

@route
def complete(state: State, week: int, day: str) -> Page:
    """
    Updates the given training session as complete in the state

    Arg:
      state[State]: the current state
    Returns:
      Page: page displaying the user's training program for the current week
    """
    
    for session in state.training_sessions:
        if session.week == week and session.day == day:
            session.is_complete = True
    return generate_program(state)

@route
def undo(state: State, week: int, day: str) -> Page:
    """
    Updates the given training session as not complete in the state
    
    Arg:
      state[State]: the current state
    Returns:
      Page: page displaying the user's training program for the current week
    """
    
    for session in state.training_sessions:
        if session.week == week and session.day == day:
            session.is_complete = False
    return generate_program(state)

@route
def previous_week(state: State) -> Page:
    """ 
    Move back a week, if the current week is not week 1
    
    Arg:
      state[State]: the current state
    Returns:
      Page: showing the traning program for the previous week
    """
    
    if state.current_week > 1:
        state.current_week -= 1
    return generate_program(state)

@route
def next_week(state: State) -> Page:
    """ 
    Move to the next week, if it's not the last week of the program
    
    Arg:
      state[State]: the current state
    Returns:
      Page: showing the traning program for the next week
    """
    
    if state.current_week < state.runner.weeks:
        state.current_week += 1
    return generate_program(state)

@route
def progress(state: State) -> Page:
    """ 
    Shows the user's total distance (based on completed sessions) and number of sessions completed, and a message

    Arg:
      state[State]: the current state
    Returns:
      Page: page showing the user's total distance and number of completed sessions
    """
    
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
    elif len(state.training_sessions) > 0 and (completed_sessions / len(state.training_sessions)) > 0.5:
        state.message = "You're making progress! Let's keep going"
    else:
        state.message = "You're doing awesome! Let's keep it up!" 
    
    statistics = Div(
        bold("You have completed: "), str(completed_sessions), "/", str(int(total_sessions)), "sessions",
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


#assert_equal tests

# validate_goal_time
assert_equal(validate_goal_time("25.5"), True)
assert_equal(validate_goal_time("abc"), False)
assert_equal(validate_goal_time(" "), False)


# validate_realistic_time
assert_equal(validate_realistic_time(5.0, 9.9), False)
assert_equal(validate_realistic_time(5.0, 10.0), True)
assert_equal(validate_realistic_time(21.1, 44.0), False)


# get_runner_level
assert_equal(get_runner_level("I'm completely new to running"), 1)
assert_equal(get_runner_level("About 5km"), 2)
assert_equal(get_runner_level("More than 10km"), 3)


# validate_training_goal
assert_equal(validate_training_goal(5.0, 1, 4, 3), True)
assert_equal(validate_training_goal(10.0, 1, 4, 3), False)
assert_equal(validate_training_goal(21.1, 2, 4, 4), True)


# get_time_message
assert_equal(
    get_time_message(Runner(5.0, "Finish the distance", 0.0, 1, 4, 3)),
    "Your goal is to finish the distance."
)
assert_equal(
    get_time_message(Runner(5.0, "Finish in a target time", 25.5, 1, 4, 3)),
    "Your target time is 25.5 minutes."
)
assert_equal(
    get_time_message(Runner(10.0, "Finish in a target time", 50.0, 2, 6, 4)),
    "Your target time is 50.0 minutes."
)


# get_easy_run_distances
assert_equal(
    get_easy_run_distances(State(Runner(5.0, "", 0.0, 1, 4, 3), [], 1, "")),
    (1.5, 3.0)
)
assert_equal(
    get_easy_run_distances(State(Runner(10.0, "", 0.0, 2, 6, 4), [], 1, "")),
    (4.0, 7.0)
)
assert_equal(
    get_easy_run_distances(State(Runner(21.1, "", 0.0, 3, 8, 5), [], 1, "")),
    (8.0, 14.0)
)


# get_workout_type
assert_equal(
    get_workout_type(State(Runner(5.0, "", 0.0, 1, 4, 3), [], 1, ""), 1),
    "Run/walk"
)
assert_equal(
    get_workout_type(State(Runner(10.0, "", 0.0, 2, 6, 4), [], 1, ""), 2),
    "Intervals"
)
assert_equal(
    get_workout_type(State(Runner(21.1, "", 0.0, 3, 8, 5), [], 1, ""), 1),
    "Intervals"
)


# get_warmup_cooldown
assert_equal(
    get_warmup_cooldown(State(Runner(5.0, "", 0.0, 1, 4, 3), [], 1, "")),
    (1, 1)
)
assert_equal(
    get_warmup_cooldown(State(Runner(10.0, "", 0.0, 2, 6, 4), [], 1, "")),
    (2, 1)
)
assert_equal(
    get_warmup_cooldown(State(Runner(21.1, "", 0.0, 2, 8, 5), [], 1, "")),
    (2, 2)
)


# get_interval_distances
assert_equal(
    get_interval_distances(State(Runner(5.0, "", 0.0, 2, 4, 3), [], 1, ""), 1),
    (500, 700)
)
assert_equal(
    get_interval_distances(State(Runner(10.0, "", 0.0, 1, 6, 4), [], 1, ""), 1),
    (800, 1500)
)
assert_equal(
    get_interval_distances(State(Runner(21.1, "", 0.0, 3, 8, 5), [], 1, ""), 2),
    (1000, 1600)
)


# get_long_run_distances
assert_equal(
    get_long_run_distances(State(Runner(5.0, "", 0.0, 1, 4, 3), [], 1, "")),
    (2.0, 4.5)
)
assert_equal(
    get_long_run_distances(State(Runner(10.0, "", 0.0, 2, 6, 4), [], 1, "")),
    (5.0, 9.0)
)
assert_equal(
    get_long_run_distances(State(Runner(21.1, "", 0.0, 3, 8, 5), [], 1, "")),
    (12.0, 18.0)
)


# get_weekly_schedule
assert_equal(
    len(get_weekly_schedule(
        State(Runner(5.0, "", 0.0, 1, 4, 3), [], 1, "")
    )),
    7
)
assert_equal(
    get_weekly_schedule(
        State(Runner(10.0, "", 0.0, 2, 6, 4), [], 1, "")
    )[2],
    REST_SESSION
)
assert_equal(
    get_weekly_schedule(
        State(Runner(21.1, "", 0.0, 3, 8, 6), [], 1, "")
    )[6],
    REST_SESSION
)

#format_face
assert_equal(format_pace(5.5), "5:30 min/km")
assert_equal(format_pace(4.25), "4:15 min/km")
assert_equal(format_pace(6.0), "6:00 min/km")

# easy_run
assert_equal(
    easy_run(State(Runner(5.0, "Finish the distance", 0.0, 1, 4, 3), [], 1, "")
),
    ("Easy run: \n1.5km @ a comfortable pace", 1.5))

# workout
assert_equal(
    workout(State(Runner(5.0, "Finish the distance", 0.0, 1, 4, 3), [], 1, ""), 1),
    (
        "Workout: \n"
        "1km warm-up @ comfortable effort\n"
        "4 x (1 min run + 2 min walk)\n"
        "1km cool-down @ very comfortable effort",
        3.3714285714285714
    )
)

# long_run
assert_equal(
    long_run(State(Runner(5.0, "Finish the distance", 0.0, 1, 4, 3), [], 1, "")),
    ("Long run: \n2.0km @ a comfortable pace", 2.0)
)


#index 
assert_equal(index(State(
    runner=Runner(distance=0.0, goal='', time=0.0, level=0, weeks=0, days=0),
    training_sessions=[],
    current_week=1,
    message=''
)), Page(State(
    runner=Runner(distance=0.0, goal='', time=0.0, level=0, weeks=0, days=0),
    training_sessions=[],
    current_week=1,
    message=''
), [
    change_color(Header("My Running Program"), "black"),
    bold("Welcome! \n"),
    "Want to take your running to the next level?",
    "\n Get a personalized running program based on your current fitness and goals! \n",
    "\n",
    Button("Let's get started", "start")
]))


#start
assert_equal(
    start(State(
        runner=Runner(
            distance=0.0,
            goal='',
            time=0.0,
            level=0,
            weeks=0,
            days=0
        ),
        training_sessions=[],
        current_week=1,
        message=''
    )),
    Page(
        State(
            runner=Runner(
                distance=0.0,
                goal='',
                time=0.0,
                level=0,
                weeks=0,
                days=0
            ),
            training_sessions=[],
            current_week=1,
            message=''
        ),
        [
            Header("Let's get started!", style_color='black'),
            bold("Let's start with some information about you. \n"),
            '',
            "\n What's your goal distance?",
            SelectBox('goal_distance', ['5.0', '10.0', '21.1'], ''),
            'km',
            "\n What's your main goal?",
            SelectBox('main_goal', ['Finish the distance', 'Finish in a target time'], ''),
            "\n If your goal is to finish in a target time, what's your target finish time (in minutes)?\n",
            italic('For example, enter 25.5 for 25 minutes and 30 seconds.'),
            TextBox('goal_time', ' '),
            "\n What's your longest continuous run so far?",
            SelectBox('longest_run', ["I'm completely new to running", 'About 5km', 'More than 10km'], ''),
            '\n In how many weeks do you want to reach your goal?',
            SelectBox('number_of_weeks', ['4', '6', '8'], ''),
            '\n How many days per week do you want to run?',
            SelectBox('days_per_week', ['3', '4', '5', '6'], ''),
            '\n',
            Button('Enter', 'enter')
        ]
    )
)

#enter
assert_equal(
    enter(
        State(
            runner=Runner(
                distance=0.0,
                goal='',
                time=0.0,
                level=0,
                weeks=0,
                days=0
            ),
            training_sessions=[],
            current_week=1,
            message=''
        ),
        '5.0',
        'Finish the distance',
        ' ',
        "I'm completely new to running",
        '4',
        '3'
    ),
    Page(
        State(
            runner=Runner(
                distance=5.0,
                goal='Finish the distance',
                time=0.0,
                level=1,
                weeks=4,
                days=3
            ),
            training_sessions=[],
            current_week=1,
            message=''
        ),
        [
            Header('Great!', style_color='black'),
            'You selected a 4-week program for 5.0 km.',
            'Your goal is to finish the distance.',
            '\n',
            '\n',
            Button("Yes! Let's go!", 'generate_program'),
            Button('No, I want to change the information', 'change')
        ]
    )
)

#change
assert_equal(
    change(
        State(
            runner=Runner(
                distance=5.0,
                goal='Finish the distance',
                time=0.0,
                level=1,
                weeks=4,
                days=3
            ),
            training_sessions=[],
            current_week=1,
            message=''
        )
    ),
    Page(
        State(
            runner=Runner(
                distance=5.0,
                goal='Finish the distance',
                time=0.0,
                level=1,
                weeks=4,
                days=3
            ),
            training_sessions=[],
            current_week=1,
            message=''
        ),
        [
            Header("Let's get started!", style_color='black'),
            bold("Let's start with some information about you. \n"),
            '',
            "\n What's your goal distance?",
            SelectBox('goal_distance', ['5.0', '10.0', '21.1'], ''),
            'km',
            "\n What's your main goal?",
            SelectBox('main_goal', ['Finish the distance', 'Finish in a target time'], ''),
            "\n If your goal is to finish in a target time, what's your target finish time (in minutes)?\n",
            italic('For example, enter 25.5 for 25 minutes and 30 seconds.'),
            TextBox('goal_time', ' '),
            "\n What's your longest continuous run so far?",
            SelectBox('longest_run', ["I'm completely new to running", 'About 5km', 'More than 10km'], ''),
            '\n In how many weeks do you want to reach your goal?',
            SelectBox('number_of_weeks', ['4', '6', '8'], ''),
            '\n How many days per week do you want to run?',
            SelectBox('days_per_week', ['3', '4', '5', '6'], ''),
            '\n',
            Button('Enter', 'enter')
        ]
    )
)

#generate_program
assert_equal(
    generate_program(
        State(
            runner=Runner(
                distance=5.0,
                goal='Finish the distance',
                time=0.0,
                level=1,
                weeks=4,
                days=3
            ),
            training_sessions=[],
            current_week=1,
            message=''
        )
    ),
    Page(
        State(
            runner=Runner(
                distance=5.0,
                goal='Finish the distance',
                time=0.0,
                level=1,
                weeks=4,
                days=3
            ),
            training_sessions=[
                TrainingSession(1, 'Monday', 'Easy run: \n1.5km @ a comfortable pace', 1.5, False),
                TrainingSession(1, 'Tuesday', 'Rest', 0.0, False),
                TrainingSession(1, 'Wednesday', 'Workout: \n1km warm-up @ comfortable effort\n4 x (1 min run + 2 min walk)\n1km cool-down @ very comfortable effort', 3.3714285714285714, False),
                TrainingSession(1, 'Thursday', 'Rest', 0.0, False),
                TrainingSession(1, 'Friday', 'Rest', 0.0, False),
                TrainingSession(1, 'Saturday', 'Long run: \n2.0km @ a comfortable pace', 2.0, False),
                TrainingSession(1, 'Sunday', 'Rest', 0.0, False),

                TrainingSession(2, 'Monday', 'Easy run: \n2.0km @ a comfortable pace', 2.0, False),
                TrainingSession(2, 'Tuesday', 'Rest', 0.0, False),
                TrainingSession(2, 'Wednesday', 'Workout: \n1km warm-up @ comfortable effort\n5 x (2 min run + 2 min walk)\n1km cool-down @ very comfortable effort', 4.428571428571429, False),
                TrainingSession(2, 'Thursday', 'Rest', 0.0, False),
                TrainingSession(2, 'Friday', 'Rest', 0.0, False),
                TrainingSession(2, 'Saturday', 'Long run: \n2.8km @ a comfortable pace', 2.8, False),
                TrainingSession(2, 'Sunday', 'Rest', 0.0, False),

                TrainingSession(3, 'Monday', 'Easy run: \n2.5km @ a comfortable pace', 2.5, False),
                TrainingSession(3, 'Tuesday', 'Rest', 0.0, False),
                TrainingSession(3, 'Wednesday', 'Workout: \n1km warm-up @ comfortable effort\n5 x (3 min run + 1 min walk)\n1km cool-down @ very comfortable effort', 4.642857142857142, False),
                TrainingSession(3, 'Thursday', 'Rest', 0.0, False),
                TrainingSession(3, 'Friday', 'Rest', 0.0, False),
                TrainingSession(3, 'Saturday', 'Long run: \n3.7km @ a comfortable pace', 3.7, False),
                TrainingSession(3, 'Sunday', 'Rest', 0.0, False),

                TrainingSession(4, 'Monday', 'Easy run: \n3.0km @ a comfortable pace', 3.0, False),
                TrainingSession(4, 'Tuesday', 'Rest', 0.0, False),
                TrainingSession(4, 'Wednesday', 'Workout: \n1km warm-up @ comfortable effort\n6 x (4 min run + 1 min walk)\n1km cool-down @ very comfortable effort', 6.0285714285714285, False),
                TrainingSession(4, 'Thursday', 'Rest', 0.0, False),
                TrainingSession(4, 'Friday', 'Rest', 0.0, False),
                TrainingSession(4, 'Saturday', 'Long run: \n4.5km @ a comfortable pace', 4.5, False),
                TrainingSession(4, 'Sunday', 'Rest', 0.0, False)
            ],
            current_week=1,
            message=''
        ),
        [
            Header('Your training schedule', style_color='black'),
            bold('Week: '),
            '1',
            ' of ',
            '4',
            Table([
                [
                    change_color(bold('Monday'), 'black'),
                    change_color(bold('Tuesday'), 'black'),
                    change_color(bold('Wednesday'), 'black'),
                    change_color(bold('Thursday'), 'black'),
                    change_color(bold('Friday'), 'black'),
                    change_color(bold('Saturday'), 'black'),
                    change_color(bold('Sunday'), 'black')
                ],
                [
                    'Easy run: \n1.5km @ a comfortable pace',
                    'Rest',
                    'Workout: \n1km warm-up @ comfortable effort\n4 x (1 min run + 2 min walk)\n1km cool-down @ very comfortable effort',
                    'Rest',
                    'Rest',
                    'Long run: \n2.0km @ a comfortable pace',
                    'Rest'
                ],
                [
                    italic('Keep it easy! Use the given pace as a guideline, but go by feel.'),
                    italic('Prioritize recovery. Make sure to get enough fuel and sleep.'),
                    italic('Time to push! Challenge yourself!'),
                    italic('Prioritize recovery. Make sure to get enough fuel and sleep.'),
                    italic('Prioritize recovery. Make sure to get enough fuel and sleep.'),
                    italic('Time to get some extra mileage in!'),
                    italic('Prioritize recovery. Make sure to get enough fuel and sleep.')
                ],
                [
                    Button('Done!', 'complete', arguments={'week': 1, 'day': 'Monday'}, style_background_color='green'),
                    ' ',
                    Button('Done!', 'complete', arguments={'week': 1, 'day': 'Wednesday'}, style_background_color='green'),
                    ' ',
                    ' ',
                    Button('Done!', 'complete', arguments={'week': 1, 'day': 'Saturday'}, style_background_color='green'),
                    ' '
                ],
                ['❌', ' ', '❌', ' ', ' ', '❌', ' ']
            ]),
            Button('Next week', 'next_week'),
            '\n',
            '\n',
            Button('Change my information', 'change'),
            '\n',
            Button('View my progress', 'progress')
        ]
    )
)

#complete
assert_equal(
    complete(
        State(
            runner=Runner(
                distance=5.0,
                goal='Finish the distance',
                time=0.0,
                level=1,
                weeks=4,
                days=3
            ),
            training_sessions=[
                TrainingSession(week=1, day='Monday', workout_type='Easy run: \n1.5km @ a comfortable pace', distance=1.5, is_complete=False),
                TrainingSession(week=1, day='Tuesday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=1, day='Wednesday', workout_type='Workout: \n1km warm_up @ comfortable effort\n4 x (1 min run + 2 min walk)\n1km cool_down @ very comfortable effort', distance=3.3714285714285714, is_complete=False),
                TrainingSession(week=1, day='Thursday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=1, day='Friday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=1, day='Saturday', workout_type='Long run: \n2.0km @ a comfortable pace', distance=2.0, is_complete=False),
                TrainingSession(week=1, day='Sunday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=2, day='Monday', workout_type='Easy run: \n2.0km @ a comfortable pace', distance=2.0, is_complete=False),
                TrainingSession(week=2, day='Tuesday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=2, day='Wednesday', workout_type='Workout: \n1km warm_up @ comfortable effort\n5 x (2 min run + 2 min walk)\n1km cool_down @ very comfortable effort', distance=4.428571428571429, is_complete=False),
                TrainingSession(week=2, day='Thursday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=2, day='Friday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=2, day='Saturday', workout_type='Long run: \n2.8km @ a comfortable pace', distance=2.8, is_complete=False),
                TrainingSession(week=2, day='Sunday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=3, day='Monday', workout_type='Easy run: \n2.5km @ a comfortable pace', distance=2.5, is_complete=False),
                TrainingSession(week=3, day='Tuesday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=3, day='Wednesday', workout_type='Workout: \n1km warm_up @ comfortable effort\n5 x (3 min run + 1 min walk)\n1km cool_down @ very comfortable effort', distance=4.642857142857142, is_complete=False),
                TrainingSession(week=3, day='Thursday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=3, day='Friday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=3, day='Saturday', workout_type='Long run: \n3.7km @ a comfortable pace', distance=3.7, is_complete=False),
                TrainingSession(week=3, day='Sunday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=4, day='Monday', workout_type='Easy run: \n3.0km @ a comfortable pace', distance=3.0, is_complete=False),
                TrainingSession(week=4, day='Tuesday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=4, day='Wednesday', workout_type='Workout: \n1km warm_up @ comfortable effort\n6 x (4 min run + 1 min walk)\n1km cool_down @ very comfortable effort', distance=6.0285714285714285, is_complete=False),
                TrainingSession(week=4, day='Thursday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=4, day='Friday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=4, day='Saturday', workout_type='Long run: \n4.5km @ a comfortable pace', distance=4.5, is_complete=False),
                TrainingSession(week=4, day='Sunday', workout_type='Rest', distance=0.0, is_complete=False)
            ],
            current_week=1,
            message=''
        ),
        1,
        'Monday'
    ),
    Page(
        State(
            runner=Runner(
                distance=5.0,
                goal='Finish the distance',
                time=0.0,
                level=1,
                weeks=4,
                days=3
            ),
            training_sessions=[
                TrainingSession(week=1, day='Monday', workout_type='Easy run: \n1.5km @ a comfortable pace', distance=1.5, is_complete=True),
                TrainingSession(week=1, day='Tuesday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=1, day='Wednesday', workout_type='Workout: \n1km warm_up @ comfortable effort\n4 x (1 min run + 2 min walk)\n1km cool_down @ very comfortable effort', distance=3.3714285714285714, is_complete=False),
                TrainingSession(week=1, day='Thursday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=1, day='Friday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=1, day='Saturday', workout_type='Long run: \n2.0km @ a comfortable pace', distance=2.0, is_complete=False),
                TrainingSession(week=1, day='Sunday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=2, day='Monday', workout_type='Easy run: \n2.0km @ a comfortable pace', distance=2.0, is_complete=False),
                TrainingSession(week=2, day='Tuesday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=2, day='Wednesday', workout_type='Workout: \n1km warm_up @ comfortable effort\n5 x (2 min run + 2 min walk)\n1km cool_down @ very comfortable effort', distance=4.428571428571429, is_complete=False),
                TrainingSession(week=2, day='Thursday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=2, day='Friday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=2, day='Saturday', workout_type='Long run: \n2.8km @ a comfortable pace', distance=2.8, is_complete=False),
                TrainingSession(week=2, day='Sunday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=3, day='Monday', workout_type='Easy run: \n2.5km @ a comfortable pace', distance=2.5, is_complete=False),
                TrainingSession(week=3, day='Tuesday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=3, day='Wednesday', workout_type='Workout: \n1km warm_up @ comfortable effort\n5 x (3 min run + 1 min walk)\n1km cool_down @ very comfortable effort', distance=4.642857142857142, is_complete=False),
                TrainingSession(week=3, day='Thursday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=3, day='Friday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=3, day='Saturday', workout_type='Long run: \n3.7km @ a comfortable pace', distance=3.7, is_complete=False),
                TrainingSession(week=3, day='Sunday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=4, day='Monday', workout_type='Easy run: \n3.0km @ a comfortable pace', distance=3.0, is_complete=False),
                TrainingSession(week=4, day='Tuesday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=4, day='Wednesday', workout_type='Workout: \n1km warm_up @ comfortable effort\n6 x (4 min run + 1 min walk)\n1km cool_down @ very comfortable effort', distance=6.0285714285714285, is_complete=False),
                TrainingSession(week=4, day='Thursday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=4, day='Friday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=4, day='Saturday', workout_type='Long run: \n4.5km @ a comfortable pace', distance=4.5, is_complete=False),
                TrainingSession(week=4, day='Sunday', workout_type='Rest', distance=0.0, is_complete=False)
            ],
            current_week=1,
            message=''
        ),
        [
            Header('Your training schedule', style_color='black'),
            bold('Week: '),
            '1',
            ' of ',
            '4',
            Table([
                [
                    change_color(bold('Monday'), 'black'),
                    change_color(bold('Tuesday'), 'black'),
                    change_color(bold('Wednesday'), 'black'),
                    change_color(bold('Thursday'), 'black'),
                    change_color(bold('Friday'), 'black'),
                    change_color(bold('Saturday'), 'black'),
                    change_color(bold('Sunday'), 'black')
                ],
                [
                    'Easy run: \n1.5km @ a comfortable pace',
                    'Rest',
                    'Workout: \n1km warm_up @ comfortable effort\n4 x (1 min run + 2 min walk)\n1km cool_down @ very comfortable effort',
                    'Rest',
                    'Rest',
                    'Long run: \n2.0km @ a comfortable pace',
                    'Rest'
                ],
                [
                    italic('Keep it easy! Use the given pace as a guideline, but go by feel.'),
                    italic('Prioritize recovery. Make sure to get enough fuel and sleep.'),
                    italic('Time to push! Challenge yourself!'),
                    italic('Prioritize recovery. Make sure to get enough fuel and sleep.'),
                    italic('Prioritize recovery. Make sure to get enough fuel and sleep.'),
                    italic('Time to get some extra mileage in!'),
                    italic('Prioritize recovery. Make sure to get enough fuel and sleep.')
                ],
                [
                    Button('Undo', 'undo', arguments={'week': 1, 'day': 'Monday'}, style_background_color='darkgray'),
                    ' ',
                    Button('Done!', 'complete', arguments={'week': 1, 'day': 'Wednesday'}, style_background_color='green'),
                    ' ',
                    ' ',
                    Button('Done!', 'complete', arguments={'week': 1, 'day': 'Saturday'}, style_background_color='green'),
                    ' '
                ],
                ['✅', ' ', '❌', ' ', ' ', '❌', ' ']
            ]),
            Button('Next week', 'next_week'),
            '\n',
            '\n',
            Button('Change my information', 'change'),
            '\n',
            Button('View my progress', 'progress')
        ]
    )
)

#undo
assert_equal(
    undo(
        State(
            runner=Runner(
                distance=5.0,
                goal='Finish the distance',
                time=0.0,
                level=1,
                weeks=4,
                days=3
            ),
            training_sessions=[
                TrainingSession(week=1, day='Monday', workout_type='Easy run: \n1.5km @ a comfortable pace', distance=1.5, is_complete=True),
                TrainingSession(week=1, day='Tuesday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=1, day='Wednesday', workout_type='Workout: \n1km warm_up @ comfortable effort\n4 x (1 min run + 2 min walk)\n1km cool_down @ very comfortable effort', distance=3.3714285714285714, is_complete=False),
                TrainingSession(week=1, day='Thursday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=1, day='Friday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=1, day='Saturday', workout_type='Long run: \n2.0km @ a comfortable pace', distance=2.0, is_complete=False),
                TrainingSession(week=1, day='Sunday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=2, day='Monday', workout_type='Easy run: \n2.0km @ a comfortable pace', distance=2.0, is_complete=False),
                TrainingSession(week=2, day='Tuesday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=2, day='Wednesday', workout_type='Workout: \n1km warm_up @ comfortable effort\n5 x (2 min run + 2 min walk)\n1km cool_down @ very comfortable effort', distance=4.428571428571429, is_complete=False),
                TrainingSession(week=2, day='Thursday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=2, day='Friday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=2, day='Saturday', workout_type='Long run: \n2.8km @ a comfortable pace', distance=2.8, is_complete=False),
                TrainingSession(week=2, day='Sunday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=3, day='Monday', workout_type='Easy run: \n2.5km @ a comfortable pace', distance=2.5, is_complete=False),
                TrainingSession(week=3, day='Tuesday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=3, day='Wednesday', workout_type='Workout: \n1km warm_up @ comfortable effort\n5 x (3 min run + 1 min walk)\n1km cool_down @ very comfortable effort', distance=4.642857142857142, is_complete=False),
                TrainingSession(week=3, day='Thursday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=3, day='Friday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=3, day='Saturday', workout_type='Long run: \n3.7km @ a comfortable pace', distance=3.7, is_complete=False),
                TrainingSession(week=3, day='Sunday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=4, day='Monday', workout_type='Easy run: \n3.0km @ a comfortable pace', distance=3.0, is_complete=False),
                TrainingSession(week=4, day='Tuesday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=4, day='Wednesday', workout_type='Workout: \n1km warm_up @ comfortable effort\n6 x (4 min run + 1 min walk)\n1km cool_down @ very comfortable effort', distance=6.0285714285714285, is_complete=False),
                TrainingSession(week=4, day='Thursday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=4, day='Friday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=4, day='Saturday', workout_type='Long run: \n4.5km @ a comfortable pace', distance=4.5, is_complete=False),
                TrainingSession(week=4, day='Sunday', workout_type='Rest', distance=0.0, is_complete=False)
            ],
            current_week=1,
            message=''
        ),
        1,
        'Monday'
    ),
    Page(
        State(
            runner=Runner(
                distance=5.0,
                goal='Finish the distance',
                time=0.0,
                level=1,
                weeks=4,
                days=3
            ),
            training_sessions=[
                TrainingSession(week=1, day='Monday', workout_type='Easy run: \n1.5km @ a comfortable pace', distance=1.5, is_complete=False),
                TrainingSession(week=1, day='Tuesday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=1, day='Wednesday', workout_type='Workout: \n1km warm_up @ comfortable effort\n4 x (1 min run + 2 min walk)\n1km cool_down @ very comfortable effort', distance=3.3714285714285714, is_complete=False),
                TrainingSession(week=1, day='Thursday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=1, day='Friday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=1, day='Saturday', workout_type='Long run: \n2.0km @ a comfortable pace', distance=2.0, is_complete=False),
                TrainingSession(week=1, day='Sunday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=2, day='Monday', workout_type='Easy run: \n2.0km @ a comfortable pace', distance=2.0, is_complete=False),
                TrainingSession(week=2, day='Tuesday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=2, day='Wednesday', workout_type='Workout: \n1km warm_up @ comfortable effort\n5 x (2 min run + 2 min walk)\n1km cool_down @ very comfortable effort', distance=4.428571428571429, is_complete=False),
                TrainingSession(week=2, day='Thursday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=2, day='Friday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=2, day='Saturday', workout_type='Long run: \n2.8km @ a comfortable pace', distance=2.8, is_complete=False),
                TrainingSession(week=2, day='Sunday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=3, day='Monday', workout_type='Easy run: \n2.5km @ a comfortable pace', distance=2.5, is_complete=False),
                TrainingSession(week=3, day='Tuesday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=3, day='Wednesday', workout_type='Workout: \n1km warm_up @ comfortable effort\n5 x (3 min run + 1 min walk)\n1km cool_down @ very comfortable effort', distance=4.642857142857142, is_complete=False),
                TrainingSession(week=3, day='Thursday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=3, day='Friday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=3, day='Saturday', workout_type='Long run: \n3.7km @ a comfortable pace', distance=3.7, is_complete=False),
                TrainingSession(week=3, day='Sunday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=4, day='Monday', workout_type='Easy run: \n3.0km @ a comfortable pace', distance=3.0, is_complete=False),
                TrainingSession(week=4, day='Tuesday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=4, day='Wednesday', workout_type='Workout: \n1km warm_up @ comfortable effort\n6 x (4 min run + 1 min walk)\n1km cool_down @ very comfortable effort', distance=6.0285714285714285, is_complete=False),
                TrainingSession(week=4, day='Thursday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=4, day='Friday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=4, day='Saturday', workout_type='Long run: \n4.5km @ a comfortable pace', distance=4.5, is_complete=False),
                TrainingSession(week=4, day='Sunday', workout_type='Rest', distance=0.0, is_complete=False)
            ],
            current_week=1,
            message=''
        ),
        [
            Header('Your training schedule', style_color='black'),
            bold('Week: '),
            '1',
            ' of ',
            '4',
            Table([
                [
                    change_color(bold('Monday'), 'black'),
                    change_color(bold('Tuesday'), 'black'),
                    change_color(bold('Wednesday'), 'black'),
                    change_color(bold('Thursday'), 'black'),
                    change_color(bold('Friday'), 'black'),
                    change_color(bold('Saturday'), 'black'),
                    change_color(bold('Sunday'), 'black')
                ],
                [
                    'Easy run: \n1.5km @ a comfortable pace',
                    'Rest',
                    'Workout: \n1km warm_up @ comfortable effort\n4 x (1 min run + 2 min walk)\n1km cool_down @ very comfortable effort',
                    'Rest',
                    'Rest',
                    'Long run: \n2.0km @ a comfortable pace',
                    'Rest'
                ],
                [
                    italic('Keep it easy! Use the given pace as a guideline, but go by feel.'),
                    italic('Prioritize recovery. Make sure to get enough fuel and sleep.'),
                    italic('Time to push! Challenge yourself!'),
                    italic('Prioritize recovery. Make sure to get enough fuel and sleep.'),
                    italic('Prioritize recovery. Make sure to get enough fuel and sleep.'),
                    italic('Time to get some extra mileage in!'),
                    italic('Prioritize recovery. Make sure to get enough fuel and sleep.')
                ],
                [
                    Button('Done!', 'complete', arguments={'week': 1, 'day': 'Monday'}, style_background_color='green'),
                    ' ',
                    Button('Done!', 'complete', arguments={'week': 1, 'day': 'Wednesday'}, style_background_color='green'),
                    ' ',
                    ' ',
                    Button('Done!', 'complete', arguments={'week': 1, 'day': 'Saturday'}, style_background_color='green'),
                    ' '
                ],
                ['❌', ' ', '❌', ' ', ' ', '❌', ' ']
            ]),
            Button('Next week', 'next_week'),
            '\n',
            '\n',
            Button('Change my information', 'change'),
            '\n',
            Button('View my progress', 'progress')
        ]
    )
)

#next_week
assert_equal(
    next_week(
        State(
            runner=Runner(
                distance=5.0,
                goal='Finish the distance',
                time=0.0,
                level=1,
                weeks=4,
                days=3
            ),
            training_sessions=[
                TrainingSession(week=1, day='Monday', workout_type='Easy run: \n1.5km @ a comfortable pace', distance=1.5, is_complete=False),
                TrainingSession(week=1, day='Tuesday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=1, day='Wednesday', workout_type='Workout: \n1km warm_up @ comfortable effort\n4 x (1 min run + 2 min walk)\n1km cool_down @ very comfortable effort', distance=3.3714285714285714, is_complete=False),
                TrainingSession(week=1, day='Thursday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=1, day='Friday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=1, day='Saturday', workout_type='Long run: \n2.0km @ a comfortable pace', distance=2.0, is_complete=False),
                TrainingSession(week=1, day='Sunday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=2, day='Monday', workout_type='Easy run: \n2.0km @ a comfortable pace', distance=2.0, is_complete=False),
                TrainingSession(week=2, day='Tuesday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=2, day='Wednesday', workout_type='Workout: \n1km warm_up @ comfortable effort\n5 x (2 min run + 2 min walk)\n1km cool_down @ very comfortable effort', distance=4.428571428571429, is_complete=False),
                TrainingSession(week=2, day='Thursday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=2, day='Friday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=2, day='Saturday', workout_type='Long run: \n2.8km @ a comfortable pace', distance=2.8, is_complete=False),
                TrainingSession(week=2, day='Sunday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=3, day='Monday', workout_type='Easy run: \n2.5km @ a comfortable pace', distance=2.5, is_complete=False),
                TrainingSession(week=3, day='Tuesday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=3, day='Wednesday', workout_type='Workout: \n1km warm_up @ comfortable effort\n5 x (3 min run + 1 min walk)\n1km cool_down @ very comfortable effort', distance=4.642857142857142, is_complete=False),
                TrainingSession(week=3, day='Thursday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=3, day='Friday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=3, day='Saturday', workout_type='Long run: \n3.7km @ a comfortable pace', distance=3.7, is_complete=False),
                TrainingSession(week=3, day='Sunday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=4, day='Monday', workout_type='Easy run: \n3.0km @ a comfortable pace', distance=3.0, is_complete=False),
                TrainingSession(week=4, day='Tuesday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=4, day='Wednesday', workout_type='Workout: \n1km warm_up @ comfortable effort\n6 x (4 min run + 1 min walk)\n1km cool_down @ very comfortable effort', distance=6.0285714285714285, is_complete=False),
                TrainingSession(week=4, day='Thursday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=4, day='Friday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=4, day='Saturday', workout_type='Long run: \n4.5km @ a comfortable pace', distance=4.5, is_complete=False),
                TrainingSession(week=4, day='Sunday', workout_type='Rest', distance=0.0, is_complete=False)
            ],
            current_week=1,
            message=''
        )
    ),
    Page(
        State(
            runner=Runner(
                distance=5.0,
                goal='Finish the distance',
                time=0.0,
                level=1,
                weeks=4,
                days=3
            ),
            training_sessions=[
                TrainingSession(week=1, day='Monday', workout_type='Easy run: \n1.5km @ a comfortable pace', distance=1.5, is_complete=False),
                TrainingSession(week=1, day='Tuesday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=1, day='Wednesday', workout_type='Workout: \n1km warm_up @ comfortable effort\n4 x (1 min run + 2 min walk)\n1km cool_down @ very comfortable effort', distance=3.3714285714285714, is_complete=False),
                TrainingSession(week=1, day='Thursday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=1, day='Friday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=1, day='Saturday', workout_type='Long run: \n2.0km @ a comfortable pace', distance=2.0, is_complete=False),
                TrainingSession(week=1, day='Sunday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=2, day='Monday', workout_type='Easy run: \n2.0km @ a comfortable pace', distance=2.0, is_complete=False),
                TrainingSession(week=2, day='Tuesday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=2, day='Wednesday', workout_type='Workout: \n1km warm_up @ comfortable effort\n5 x (2 min run + 2 min walk)\n1km cool_down @ very comfortable effort', distance=4.428571428571429, is_complete=False),
                TrainingSession(week=2, day='Thursday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=2, day='Friday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=2, day='Saturday', workout_type='Long run: \n2.8km @ a comfortable pace', distance=2.8, is_complete=False),
                TrainingSession(week=2, day='Sunday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=3, day='Monday', workout_type='Easy run: \n2.5km @ a comfortable pace', distance=2.5, is_complete=False),
                TrainingSession(week=3, day='Tuesday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=3, day='Wednesday', workout_type='Workout: \n1km warm_up @ comfortable effort\n5 x (3 min run + 1 min walk)\n1km cool_down @ very comfortable effort', distance=4.642857142857142, is_complete=False),
                TrainingSession(week=3, day='Thursday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=3, day='Friday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=3, day='Saturday', workout_type='Long run: \n3.7km @ a comfortable pace', distance=3.7, is_complete=False),
                TrainingSession(week=3, day='Sunday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=4, day='Monday', workout_type='Easy run: \n3.0km @ a comfortable pace', distance=3.0, is_complete=False),
                TrainingSession(week=4, day='Tuesday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=4, day='Wednesday', workout_type='Workout: \n1km warm_up @ comfortable effort\n6 x (4 min run + 1 min walk)\n1km cool_down @ very comfortable effort', distance=6.0285714285714285, is_complete=False),
                TrainingSession(week=4, day='Thursday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=4, day='Friday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=4, day='Saturday', workout_type='Long run: \n4.5km @ a comfortable pace', distance=4.5, is_complete=False),
                TrainingSession(week=4, day='Sunday', workout_type='Rest', distance=0.0, is_complete=False)
            ],
            current_week=2,
            message=''
        ),
        [
            Header('Your training schedule', style_color='black'),
            bold('Week: '),
            '2',
            ' of ',
            '4',
            Table([
                [
                    change_color(bold('Monday'), 'black'),
                    change_color(bold('Tuesday'), 'black'),
                    change_color(bold('Wednesday'), 'black'),
                    change_color(bold('Thursday'), 'black'),
                    change_color(bold('Friday'), 'black'),
                    change_color(bold('Saturday'), 'black'),
                    change_color(bold('Sunday'), 'black')
                ],
                [
                    'Easy run: \n2.0km @ a comfortable pace',
                    'Rest',
                    'Workout: \n1km warm_up @ comfortable effort\n5 x (2 min run + 2 min walk)\n1km cool_down @ very comfortable effort',
                    'Rest',
                    'Rest',
                    'Long run: \n2.8km @ a comfortable pace',
                    'Rest'
                ],
                [
                    italic('Keep it easy! Use the given pace as a guideline, but go by feel.'),
                    italic('Prioritize recovery. Make sure to get enough fuel and sleep.'),
                    italic('Time to push! Challenge yourself!'),
                    italic('Prioritize recovery. Make sure to get enough fuel and sleep.'),
                    italic('Prioritize recovery. Make sure to get enough fuel and sleep.'),
                    italic('Time to get some extra mileage in!'),
                    italic('Prioritize recovery. Make sure to get enough fuel and sleep.')
                ],
                [
                    Button('Done!', 'complete', arguments={'week': 2, 'day': 'Monday'}, style_background_color='green'),
                    ' ',
                    Button('Done!', 'complete', arguments={'week': 2, 'day': 'Wednesday'}, style_background_color='green'),
                    ' ',
                    ' ',
                    Button('Done!', 'complete', arguments={'week': 2, 'day': 'Saturday'}, style_background_color='green'),
                    ' '
                ],
                ['❌', ' ', '❌', ' ', ' ', '❌', ' ']
            ]),
            Button('Previous week', 'previous_week'),
            Button('Next week', 'next_week'),
            '\n',
            '\n',
            Button('Change my information', 'change'),
            '\n',
            Button('View my progress', 'progress')
        ]
    )
)

#previous_week
assert_equal(
    previous_week(State(
        runner=Runner(
            distance=5.0,
            goal='Finish the distance',
            time=0.0,
            level=1,
            weeks=4,
            days=3
        ),
        training_sessions=[
            TrainingSession(week=1, day='Monday', workout_type='Easy run: \n1.5km @ a comfortable pace', distance=1.5, is_complete=False),
            TrainingSession(week=1, day='Tuesday', workout_type='Rest', distance=0.0, is_complete=False),
            TrainingSession(week=1, day='Wednesday', workout_type='Workout: \n1km warm_up @ comfortable effort\n4 x (1 min run + 2 min walk)\n1km cool_down @ very comfortable effort', distance=3.3714285714285714, is_complete=False),
            TrainingSession(week=1, day='Thursday', workout_type='Rest', distance=0.0, is_complete=False),
            TrainingSession(week=1, day='Friday', workout_type='Rest', distance=0.0, is_complete=False),
            TrainingSession(week=1, day='Saturday', workout_type='Long run: \n2.0km @ a comfortable pace', distance=2.0, is_complete=False),
            TrainingSession(week=1, day='Sunday', workout_type='Rest', distance=0.0, is_complete=False),
            TrainingSession(week=2, day='Monday', workout_type='Easy run: \n2.0km @ a comfortable pace', distance=2.0, is_complete=False),
            TrainingSession(week=2, day='Tuesday', workout_type='Rest', distance=0.0, is_complete=False),
            TrainingSession(week=2, day='Wednesday', workout_type='Workout: \n1km warm_up @ comfortable effort\n5 x (2 min run + 2 min walk)\n1km cool_down @ very comfortable effort', distance=4.428571428571429, is_complete=False),
            TrainingSession(week=2, day='Thursday', workout_type='Rest', distance=0.0, is_complete=False),
            TrainingSession(week=2, day='Friday', workout_type='Rest', distance=0.0, is_complete=False),
            TrainingSession(week=2, day='Saturday', workout_type='Long run: \n2.8km @ a comfortable pace', distance=2.8, is_complete=False),
            TrainingSession(week=2, day='Sunday', workout_type='Rest', distance=0.0, is_complete=False),
            TrainingSession(week=3, day='Monday', workout_type='Easy run: \n2.5km @ a comfortable pace', distance=2.5, is_complete=False),
            TrainingSession(week=3, day='Tuesday', workout_type='Rest', distance=0.0, is_complete=False),
            TrainingSession(week=3, day='Wednesday', workout_type='Workout: \n1km warm_up @ comfortable effort\n5 x (3 min run + 1 min walk)\n1km cool_down @ very comfortable effort', distance=4.642857142857142, is_complete=False),
            TrainingSession(week=3, day='Thursday', workout_type='Rest', distance=0.0, is_complete=False),
            TrainingSession(week=3, day='Friday', workout_type='Rest', distance=0.0, is_complete=False),
            TrainingSession(week=3, day='Saturday', workout_type='Long run: \n3.7km @ a comfortable pace', distance=3.7, is_complete=False),
            TrainingSession(week=3, day='Sunday', workout_type='Rest', distance=0.0, is_complete=False),
            TrainingSession(week=4, day='Monday', workout_type='Easy run: \n3.0km @ a comfortable pace', distance=3.0, is_complete=False),
            TrainingSession(week=4, day='Tuesday', workout_type='Rest', distance=0.0, is_complete=False),
            TrainingSession(week=4, day='Wednesday', workout_type='Workout: \n1km warm_up @ comfortable effort\n6 x (4 min run + 1 min walk)\n1km cool_down @ very comfortable effort', distance=6.0285714285714285, is_complete=False),
            TrainingSession(week=4, day='Thursday', workout_type='Rest', distance=0.0, is_complete=False),
            TrainingSession(week=4, day='Friday', workout_type='Rest', distance=0.0, is_complete=False),
            TrainingSession(week=4, day='Saturday', workout_type='Long run: \n4.5km @ a comfortable pace', distance=4.5, is_complete=False),
            TrainingSession(week=4, day='Sunday', workout_type='Rest', distance=0.0, is_complete=False)
        ],
        current_week=2,
        message=''
    )),
    Page(
        state=State(
            runner=Runner(distance=5.0, goal='Finish the distance', time=0.0, level=1, weeks=4, days=3),
            training_sessions=[
                TrainingSession(week=1, day='Monday', workout_type='Easy run: \n1.5km @ a comfortable pace', distance=1.5, is_complete=False),
                TrainingSession(week=1, day='Tuesday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=1, day='Wednesday', workout_type='Workout: \n1km warm_up @ comfortable effort\n4 x (1 min run + 2 min walk)\n1km cool_down @ very comfortable effort', distance=3.3714285714285714, is_complete=False),
                TrainingSession(week=1, day='Thursday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=1, day='Friday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=1, day='Saturday', workout_type='Long run: \n2.0km @ a comfortable pace', distance=2.0, is_complete=False),
                TrainingSession(week=1, day='Sunday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=2, day='Monday', workout_type='Easy run: \n2.0km @ a comfortable pace', distance=2.0, is_complete=False),
                TrainingSession(week=2, day='Tuesday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=2, day='Wednesday', workout_type='Workout: \n1km warm_up @ comfortable effort\n5 x (2 min run + 2 min walk)\n1km cool_down @ very comfortable effort', distance=4.428571428571429, is_complete=False),
                TrainingSession(week=2, day='Thursday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=2, day='Friday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=2, day='Saturday', workout_type='Long run: \n2.8km @ a comfortable pace', distance=2.8, is_complete=False),
                TrainingSession(week=2, day='Sunday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=3, day='Monday', workout_type='Easy run: \n2.5km @ a comfortable pace', distance=2.5, is_complete=False),
                TrainingSession(week=3, day='Tuesday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=3, day='Wednesday', workout_type='Workout: \n1km warm_up @ comfortable effort\n5 x (3 min run + 1 min walk)\n1km cool_down @ very comfortable effort', distance=4.642857142857142, is_complete=False),
                TrainingSession(week=3, day='Thursday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=3, day='Friday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=3, day='Saturday', workout_type='Long run: \n3.7km @ a comfortable pace', distance=3.7, is_complete=False),
                TrainingSession(week=3, day='Sunday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=4, day='Monday', workout_type='Easy run: \n3.0km @ a comfortable pace', distance=3.0, is_complete=False),
                TrainingSession(week=4, day='Tuesday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=4, day='Wednesday', workout_type='Workout: \n1km warm_up @ comfortable effort\n6 x (4 min run + 1 min walk)\n1km cool_down @ very comfortable effort', distance=6.0285714285714285, is_complete=False),
                TrainingSession(week=4, day='Thursday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=4, day='Friday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=4, day='Saturday', workout_type='Long run: \n4.5km @ a comfortable pace', distance=4.5, is_complete=False),
                TrainingSession(week=4, day='Sunday', workout_type='Rest', distance=0.0, is_complete=False)
            ],
            current_week=1,
            message=''
        ),
        content=[
            Header('Your training schedule', style_color='black'),
            bold('Week: '),
            '1',
            ' of ',
            '4',
            Table([
                [
                    change_color(bold('Monday'), 'black'),
                    change_color(bold('Tuesday'), 'black'),
                    change_color(bold('Wednesday'), 'black'),
                    change_color(bold('Thursday'), 'black'),
                    change_color(bold('Friday'), 'black'),
                    change_color(bold('Saturday'), 'black'),
                    change_color(bold('Sunday'), 'black')
                ],
                [
                    'Easy run: \n1.5km @ a comfortable pace',
                    'Rest',
                    'Workout: \n1km warm_up @ comfortable effort\n4 x (1 min run + 2 min walk)\n1km cool_down @ very comfortable effort',
                    'Rest',
                    'Rest',
                    'Long run: \n2.0km @ a comfortable pace',
                    'Rest'
                ],
                [
                    italic('Keep it easy! Use the given pace as a guideline, but go by feel.'),
                    italic('Prioritize recovery. Make sure to get enough fuel and sleep.'),
                    italic('Time to push! Challenge yourself!'),
                    italic('Prioritize recovery. Make sure to get enough fuel and sleep.'),
                    italic('Prioritize recovery. Make sure to get enough fuel and sleep.'),
                    italic('Time to get some extra mileage in!'),
                    italic('Prioritize recovery. Make sure to get enough fuel and sleep.')
                ],
                [
                    Button('Done!', 'complete', arguments={'week': 1, 'day': 'Monday'}, style_background_color='green'),
                    ' ',
                    Button('Done!', 'complete', arguments={'week': 1, 'day': 'Wednesday'}, style_background_color='green'),
                    ' ',
                    ' ',
                    Button('Done!', 'complete', arguments={'week': 1, 'day': 'Saturday'}, style_background_color='green'),
                    ' '
                ],
                ['❌', ' ', '❌', ' ', ' ', '❌', ' ']
            ]),
            Button('Next week', 'next_week'),
            '\n',
            '\n',
            Button('Change my information', 'change'),
            '\n',
            Button('View my progress', 'progress')
        ]
    )
)

#progress
assert_equal(
    progress(State(
        runner=Runner(distance=5.0, goal='Finish the distance', time=0.0, level=1, weeks=4, days=3),
        training_sessions=[
            TrainingSession(week=1, day='Monday', workout_type='Easy run: \n1.5km @ a comfortable pace', distance=1.5, is_complete=False),
            TrainingSession(week=1, day='Tuesday', workout_type='Rest', distance=0.0, is_complete=False),
            TrainingSession(week=1, day='Wednesday', workout_type='Workout: \n1km warm_up @ comfortable effort\n4 x (1 min run + 2 min walk)\n1km cool_down @ very comfortable effort', distance=3.3714285714285714, is_complete=False),
            TrainingSession(week=1, day='Thursday', workout_type='Rest', distance=0.0, is_complete=False),
            TrainingSession(week=1, day='Friday', workout_type='Rest', distance=0.0, is_complete=False),
            TrainingSession(week=1, day='Saturday', workout_type='Long run: \n2.0km @ a comfortable pace', distance=2.0, is_complete=False),
            TrainingSession(week=1, day='Sunday', workout_type='Rest', distance=0.0, is_complete=False),
            TrainingSession(week=2, day='Monday', workout_type='Easy run: \n2.0km @ a comfortable pace', distance=2.0, is_complete=False),
            TrainingSession(week=2, day='Tuesday', workout_type='Rest', distance=0.0, is_complete=False),
            TrainingSession(week=2, day='Wednesday', workout_type='Workout: \n1km warm_up @ comfortable effort\n5 x (2 min run + 2 min walk)\n1km cool_down @ very comfortable effort', distance=4.428571428571429, is_complete=False),
            TrainingSession(week=2, day='Thursday', workout_type='Rest', distance=0.0, is_complete=False),
            TrainingSession(week=2, day='Friday', workout_type='Rest', distance=0.0, is_complete=False),
            TrainingSession(week=2, day='Saturday', workout_type='Long run: \n2.8km @ a comfortable pace', distance=2.8, is_complete=False),
            TrainingSession(week=2, day='Sunday', workout_type='Rest', distance=0.0, is_complete=False),
            TrainingSession(week=3, day='Monday', workout_type='Easy run: \n2.5km @ a comfortable pace', distance=2.5, is_complete=False),
            TrainingSession(week=3, day='Tuesday', workout_type='Rest', distance=0.0, is_complete=False),
            TrainingSession(week=3, day='Wednesday', workout_type='Workout: \n1km warm_up @ comfortable effort\n5 x (3 min run + 1 min walk)\n1km cool_down @ very comfortable effort', distance=4.642857142857142, is_complete=False),
            TrainingSession(week=3, day='Thursday', workout_type='Rest', distance=0.0, is_complete=False),
            TrainingSession(week=3, day='Friday', workout_type='Rest', distance=0.0, is_complete=False),
            TrainingSession(week=3, day='Saturday', workout_type='Long run: \n3.7km @ a comfortable pace', distance=3.7, is_complete=False),
            TrainingSession(week=3, day='Sunday', workout_type='Rest', distance=0.0, is_complete=False),
            TrainingSession(week=4, day='Monday', workout_type='Easy run: \n3.0km @ a comfortable pace', distance=3.0, is_complete=False),
            TrainingSession(week=4, day='Tuesday', workout_type='Rest', distance=0.0, is_complete=False),
            TrainingSession(week=4, day='Wednesday', workout_type='Workout: \n1km warm_up @ comfortable effort\n6 x (4 min run + 1 min walk)\n1km cool_down @ very comfortable effort', distance=6.0285714285714285, is_complete=False),
            TrainingSession(week=4, day='Thursday', workout_type='Rest', distance=0.0, is_complete=False),
            TrainingSession(week=4, day='Friday', workout_type='Rest', distance=0.0, is_complete=False),
            TrainingSession(week=4, day='Saturday', workout_type='Long run: \n4.5km @ a comfortable pace', distance=4.5, is_complete=False),
            TrainingSession(week=4, day='Sunday', workout_type='Rest', distance=0.0, is_complete=False)
        ],
        current_week=1,
        message=''
    )),
    Page(
        state=State(
            runner=Runner(distance=5.0, goal='Finish the distance', time=0.0, level=1, weeks=4, days=3),
            training_sessions=[
                TrainingSession(week=1, day='Monday', workout_type='Easy run: \n1.5km @ a comfortable pace', distance=1.5, is_complete=False),
                TrainingSession(week=1, day='Tuesday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=1, day='Wednesday', workout_type='Workout: \n1km warm_up @ comfortable effort\n4 x (1 min run + 2 min walk)\n1km cool_down @ very comfortable effort', distance=3.3714285714285714, is_complete=False),
                TrainingSession(week=1, day='Thursday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=1, day='Friday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=1, day='Saturday', workout_type='Long run: \n2.0km @ a comfortable pace', distance=2.0, is_complete=False),
                TrainingSession(week=1, day='Sunday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=2, day='Monday', workout_type='Easy run: \n2.0km @ a comfortable pace', distance=2.0, is_complete=False),
                TrainingSession(week=2, day='Tuesday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=2, day='Wednesday', workout_type='Workout: \n1km warm_up @ comfortable effort\n5 x (2 min run + 2 min walk)\n1km cool_down @ very comfortable effort', distance=4.428571428571429, is_complete=False),
                TrainingSession(week=2, day='Thursday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=2, day='Friday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=2, day='Saturday', workout_type='Long run: \n2.8km @ a comfortable pace', distance=2.8, is_complete=False),
                TrainingSession(week=2, day='Sunday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=3, day='Monday', workout_type='Easy run: \n2.5km @ a comfortable pace', distance=2.5, is_complete=False),
                TrainingSession(week=3, day='Tuesday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=3, day='Wednesday', workout_type='Workout: \n1km warm_up @ comfortable effort\n5 x (3 min run + 1 min walk)\n1km cool_down @ very comfortable effort', distance=4.642857142857142, is_complete=False),
                TrainingSession(week=3, day='Thursday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=3, day='Friday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=3, day='Saturday', workout_type='Long run: \n3.7km @ a comfortable pace', distance=3.7, is_complete=False),
                TrainingSession(week=3, day='Sunday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=4, day='Monday', workout_type='Easy run: \n3.0km @ a comfortable pace', distance=3.0, is_complete=False),
                TrainingSession(week=4, day='Tuesday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=4, day='Wednesday', workout_type='Workout: \n1km warm_up @ comfortable effort\n6 x (4 min run + 1 min walk)\n1km cool_down @ very comfortable effort', distance=6.0285714285714285, is_complete=False),
                TrainingSession(week=4, day='Thursday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=4, day='Friday', workout_type='Rest', distance=0.0, is_complete=False),
                TrainingSession(week=4, day='Saturday', workout_type='Long run: \n4.5km @ a comfortable pace', distance=4.5, is_complete=False),
                TrainingSession(week=4, day='Sunday', workout_type='Rest', distance=0.0, is_complete=False)
            ],
            current_week=1,
            message="It's your first week! You're doing great!"
        ),
        content=[
            Header('Your progress', style_color='black'),
            "It's your first week! You're doing great!",
            '\n',
            Div(
                bold('You have completed: '),
                '0',
                '/',
                '12',
                'sessions',
                '\n',
                bold('Total distance: '),
                '0.0',
                'km',
                style_border='2px solid steelblue',
                style_padding='12px',
                style_width='500px'
            ),
            '\n',
            Button('Back to schedule', 'generate_program')
        ]
    )
)

start_server(State(Runner(0.0, "", 0.0, 0, 0, 0), [], 1, ""))

