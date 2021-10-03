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
