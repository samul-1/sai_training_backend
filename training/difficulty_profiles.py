from training.models import AbstractItem

(very_easy, easy, medium, hard, very_hard) = (
    AbstractItem.VERY_EASY,
    AbstractItem.EASY,
    AbstractItem.MEDIUM,
    AbstractItem.HARD,
    AbstractItem.VERY_HARD,
)

# The following two declaration are "fall-through rules": they're used to define behavior for
# when there aren't enough items of the required difficulty level to fulfill the request, so
# the function that fetches the items "falls through" the level and tries to get the remainder
# from the next one

# BOTTOM_UP instructs the function that randomly selects items to start from the lowest-valued
# difficulty level and to move upwards - this way, if a given difficulty level doesn't have the
# required number of items to supply, the function will attempt to get the remainder of the items
# from the next higher difficulty level
# TOP_DOWN does the opposite, starting from the highest-valued level and working its way down

# For example, if we need to get 2 items from EASY and 3 from MEDIUM, but there is only one
# item in MEDIUM, and we're using the BOTTOM_UP rule: we will first get the two items from
# EASY, then attempt to get three from MEDIUM but will only get one, then move higher to the next
# level (HARD) and get the remaining two items from there. If the rule had been TOP_DOWN, we would
# have gotten one from MEDIUM and four from EASY. If EASY didn't have 4 items, we would have
# fallen down to VERY_EASY

# todo what would have happened if VERY_EASY hadn't had enough items either? 3 options:
# - warped back to VERY_HARD using the modulo operator
# - warped back to the first one higher than the starting one (HARD in this case)
# - returned less total items than the requested amount


BOTTOM_UP = 1
TOP_DOWN = -1


EASY_ONLY = {
    very_easy: 0.5,
    easy: 0.5,
    "fall_through_direction": BOTTOM_UP,  # if there aren't enough `very_easy` items, add more `easy`
}

HARD_ONLY = {
    hard: 0.5,
    very_hard: 0.5,
    "fall_through_direction": TOP_DOWN,  # if there aren't enough `very_hard` items, add more `hard`
}

BALANCED = {
    very_easy: 0.2,
    easy: 0.2,
    medium: 0.2,
    hard: 0.2,
    very_hard: 0.2,
    "fall_through_direction": TOP_DOWN,  # this favors slightly easier configurations
}

MOSTLY_EASY = {
    very_easy: 0.25,
    easy: 0.30,
    medium: 0.25,
    hard: 0.10,
    very_hard: 0.10,
    # if there aren't enough (very)-hard items, this will favor even easier configurations
    "fall_through_direction": TOP_DOWN,
}

MOSTLY_HARD = {
    very_easy: 0.10,
    easy: 0.10,
    medium: 0.25,
    hard: 0.30,
    very_hard: 0.25,
    # if there aren't enough (very)-easy items, this will favor even harder configurations
    "fall_through_direction": BOTTOM_UP,
}
