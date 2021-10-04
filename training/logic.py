import math as m


def get_items(model, topic, amounts, difficulty_profile, exclude_queryset):
    from .difficulty_profiles import get_last_level_checked, get_levels_range
    from .models import AbstractItem

    ret = []

    # pass through each level twice: this is needed in case a level can't satisfy
    # the requirement and neither can any subsequent level - after looping through
    # the levels, each previously visited level has a second chance to fill in the
    # debt from the previously visited level(s)
    levels_range = get_levels_range(difficulty_profile, rounds=2)

    remainder_last_level = 0
    second_round = False
    for level in levels_range:
        level = level % (AbstractItem.VERY_HARD + 1)

        # the amount of questions needed for this level is the value in the field
        # `amount_<level_name>` plus the difference between the requested amount for
        # the previous level and the amount that was actually able to be supplied

        amount = (
            amounts.get(AbstractItem.get_difficulty_level_name(level))
            + remainder_last_level
        )

        # get random questions for given topic and difficulty level
        questions = (
            model.objects.filter(
                topic=topic,
                difficulty=level,
            )
            .exclude(pk__in=[i.id for i in ret])
            .exclude(pk__in=exclude_queryset)
            .order_by("?")[:amount]
        )
        ret.extend(questions)

        remainder_last_level = amount - questions.count()

        if level == get_last_level_checked(difficulty_profile):
            if remainder_last_level == 0:
                # we iterated over all the levels once and there aren't any
                # questions left to add - we're done
                break
            else:
                # there are leftover questions to be added: go back to the
                # first level and try to fill the gap
                second_round = True
    return ret


def get_concrete_difficulty_profile_amounts(difficulty_profile, total_amount):
    from .difficulty_profiles import get_levels_range
    from .models import AbstractItem

    ret = {}

    levels_range = get_levels_range(difficulty_profile)

    actual_total = 0
    for level in levels_range:
        try:
            actual_amount = m.floor(total_amount * difficulty_profile[level])
            actual_total += actual_amount

            ret[
                f"amount_{AbstractItem.get_difficulty_level_name(level)}"
            ] = actual_amount

        except KeyError:
            pass

    # this happens if rounding down percentages caused a lower total than the
    # requested one: distribute the remainder evenly among fields
    if actual_total < total_amount:
        difference = total_amount - actual_total

        while difference > 0:
            levels_range = get_levels_range(difficulty_profile)
            for level in levels_range:
                target_field = f"amount_{AbstractItem.get_difficulty_level_name(level)}"
                ret[target_field] = ret[target_field] + 1
                difference -= 1
                if difference == 0:
                    break

    print("RET")
    print(ret)
    return ret
