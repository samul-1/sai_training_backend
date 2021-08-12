from django.test import TestCase
from users.models import User

from training.models import (
    AbstractItem,
    Course,
    Question,
    Topic,
    TrainingSession,
    TrainingTemplate,
    TrainingTemplateRule,
)


def common_data_set_up(obj):
    obj.student = User.objects.create(
        username="student",
        email="student@studenti.unipi.it",
    )
    obj.teacher = User.objects.create(
        username="teacher",
        email="teacher@unipi.it",
    )
    obj.math_course = Course.objects.create(
        name="math",
        creator=obj.teacher,
    )
    obj.topic_trigonometry = Topic.objects.create(
        name="trigonometry",
        course=obj.math_course,
    )
    obj.topic_logarithms = Topic.objects.create(
        name="logarithms",
        course=obj.math_course,
    )
    obj.topic_exponentials = Topic.objects.create(
        name="exponentials",
        course=obj.math_course,
    )

    obj.trigo_q1 = Question.objects.create(
        text="sin(pi)=",
        topic=obj.topic_trigonometry,
        course=obj.math_course,
        difficulty=AbstractItem.EASY,
    )
    obj.trigo_q2 = Question.objects.create(
        text="cos(0)=",
        topic=obj.topic_trigonometry,
        course=obj.math_course,
        difficulty=AbstractItem.MEDIUM,
    )
    obj.log_q1 = Question.objects.create(
        text="log e=",
        topic=obj.topic_logarithms,
        course=obj.math_course,
        difficulty=AbstractItem.VERY_EASY,
    )
    obj.log_q2 = Question.objects.create(
        text="log a + log b",
        topic=obj.topic_logarithms,
        course=obj.math_course,
        difficulty=AbstractItem.HARD,
    )


class TrainingTemplateTestCase(TestCase):
    def setUp(self):
        common_data_set_up(self)

    def test_balanced_profile(self):
        template1 = TrainingTemplate.objects.create(
            name="template1",
            course=self.math_course,
        )

        # with profile balanced and amount multiple of 5, each level gets equal amount
        t1rule1 = TrainingTemplateRule.objects.create(
            amount=5,
            training_template=template1,
            difficulty_profile_code=TrainingTemplateRule.BALANCED,
            topic=self.topic_trigonometry,
        )
        self.assertEquals(t1rule1.amount_very_easy, 1)
        self.assertEquals(t1rule1.amount_easy, 1)
        self.assertEquals(t1rule1.amount_medium, 1)
        self.assertEquals(t1rule1.amount_hard, 1)
        self.assertEquals(t1rule1.amount_very_hard, 1)
        t1rule1.delete()

        # if amount cannot be integer-divided for all levels (e.g. the value for some
        # fields would be rounded down to zero), the remainder gets evenly distributed
        t1rule2 = TrainingTemplateRule.objects.create(
            amount=4,
            training_template=template1,
            difficulty_profile_code=TrainingTemplateRule.BALANCED,
            topic=self.topic_trigonometry,
        )
        self.assertEquals(t1rule2.amount_very_easy, 0)
        self.assertEquals(t1rule2.amount_easy, 1)
        self.assertEquals(t1rule2.amount_medium, 1)
        self.assertEquals(t1rule2.amount_hard, 1)
        self.assertEquals(t1rule2.amount_very_hard, 1)
        t1rule2.delete()

        t1rule3 = TrainingTemplateRule.objects.create(
            amount=7,
            training_template=template1,
            difficulty_profile_code=TrainingTemplateRule.BALANCED,
            topic=self.topic_trigonometry,
        )
        self.assertEquals(t1rule3.amount_very_easy, 1)
        self.assertEquals(t1rule3.amount_easy, 1)
        self.assertEquals(t1rule3.amount_medium, 1)
        self.assertEquals(t1rule3.amount_hard, 2)
        self.assertEquals(t1rule3.amount_very_hard, 2)
        t1rule3.delete()

        t1rule4 = TrainingTemplateRule.objects.create(
            amount=1,
            training_template=template1,
            difficulty_profile_code=TrainingTemplateRule.BALANCED,
            topic=self.topic_trigonometry,
        )
        self.assertEquals(t1rule4.amount_very_easy, 0)
        self.assertEquals(t1rule4.amount_easy, 0)
        self.assertEquals(t1rule4.amount_medium, 0)
        self.assertEquals(t1rule4.amount_hard, 0)
        self.assertEquals(t1rule4.amount_very_hard, 1)
        t1rule4.delete()

    def test_easy_only_profile(self):
        template1 = TrainingTemplate.objects.create(
            name="template1",
            course=self.math_course,
        )

        t1rule1 = TrainingTemplateRule.objects.create(
            amount=5,
            training_template=template1,
            difficulty_profile_code=TrainingTemplateRule.EASY_ONLY,
            topic=self.topic_trigonometry,
        )
        self.assertEquals(t1rule1.amount_very_easy, 2)
        self.assertEquals(t1rule1.amount_easy, 3)
        self.assertEquals(t1rule1.amount_medium, 0)
        self.assertEquals(t1rule1.amount_hard, 0)
        self.assertEquals(t1rule1.amount_very_hard, 0)
        t1rule1.delete()

        t1rule2 = TrainingTemplateRule.objects.create(
            amount=2,
            training_template=template1,
            difficulty_profile_code=TrainingTemplateRule.EASY_ONLY,
            topic=self.topic_trigonometry,
        )
        self.assertEquals(t1rule2.amount_very_easy, 1)
        self.assertEquals(t1rule2.amount_easy, 1)
        self.assertEquals(t1rule2.amount_medium, 0)
        self.assertEquals(t1rule2.amount_hard, 0)
        self.assertEquals(t1rule2.amount_very_hard, 0)
        t1rule2.delete()

        t1rule3 = TrainingTemplateRule.objects.create(
            amount=1,
            training_template=template1,
            difficulty_profile_code=TrainingTemplateRule.EASY_ONLY,
            topic=self.topic_trigonometry,
        )
        self.assertEquals(t1rule3.amount_very_easy, 1)
        self.assertEquals(t1rule3.amount_easy, 0)
        self.assertEquals(t1rule3.amount_medium, 0)
        self.assertEquals(t1rule3.amount_hard, 0)
        self.assertEquals(t1rule3.amount_very_hard, 0)
        t1rule3.delete()

        t1rule4 = TrainingTemplateRule.objects.create(
            amount=9,
            training_template=template1,
            difficulty_profile_code=TrainingTemplateRule.EASY_ONLY,
            topic=self.topic_trigonometry,
        )
        self.assertEquals(t1rule4.amount_very_easy, 4)
        self.assertEquals(t1rule4.amount_easy, 5)
        self.assertEquals(t1rule4.amount_medium, 0)
        self.assertEquals(t1rule4.amount_hard, 0)
        self.assertEquals(t1rule4.amount_very_hard, 0)
        t1rule4.delete()

    def test_hard_only_profile(self):
        template1 = TrainingTemplate.objects.create(
            name="template1",
            course=self.math_course,
        )

        t1rule1 = TrainingTemplateRule.objects.create(
            amount=5,
            training_template=template1,
            difficulty_profile_code=TrainingTemplateRule.HARD_ONLY,
            topic=self.topic_trigonometry,
        )
        self.assertEquals(t1rule1.amount_very_easy, 0)
        self.assertEquals(t1rule1.amount_easy, 0)
        self.assertEquals(t1rule1.amount_medium, 0)
        self.assertEquals(t1rule1.amount_hard, 3)
        self.assertEquals(t1rule1.amount_very_hard, 2)
        t1rule1.delete()

        t1rule2 = TrainingTemplateRule.objects.create(
            amount=2,
            training_template=template1,
            difficulty_profile_code=TrainingTemplateRule.HARD_ONLY,
            topic=self.topic_trigonometry,
        )
        self.assertEquals(t1rule2.amount_very_easy, 0)
        self.assertEquals(t1rule2.amount_easy, 0)
        self.assertEquals(t1rule2.amount_medium, 0)
        self.assertEquals(t1rule2.amount_hard, 1)
        self.assertEquals(t1rule2.amount_very_hard, 1)
        t1rule2.delete()

        t1rule3 = TrainingTemplateRule.objects.create(
            amount=1,
            training_template=template1,
            difficulty_profile_code=TrainingTemplateRule.HARD_ONLY,
            topic=self.topic_trigonometry,
        )
        self.assertEquals(t1rule3.amount_very_easy, 0)
        self.assertEquals(t1rule3.amount_easy, 0)
        self.assertEquals(t1rule3.amount_medium, 0)
        self.assertEquals(t1rule3.amount_hard, 0)
        self.assertEquals(t1rule3.amount_very_hard, 1)
        t1rule3.delete()

        t1rule4 = TrainingTemplateRule.objects.create(
            amount=9,
            training_template=template1,
            difficulty_profile_code=TrainingTemplateRule.HARD_ONLY,
            topic=self.topic_trigonometry,
        )
        self.assertEquals(t1rule4.amount_very_easy, 0)
        self.assertEquals(t1rule4.amount_easy, 0)
        self.assertEquals(t1rule4.amount_medium, 0)
        self.assertEquals(t1rule4.amount_hard, 5)
        self.assertEquals(t1rule4.amount_very_hard, 4)
        t1rule4.delete()

    def test_mostly_easy_profile(self):
        template1 = TrainingTemplate.objects.create(
            name="template1",
            course=self.math_course,
        )

        t1rule1 = TrainingTemplateRule.objects.create(
            amount=5,
            training_template=template1,
            difficulty_profile_code=TrainingTemplateRule.MOSTLY_EASY,
            topic=self.topic_trigonometry,
        )
        self.assertEquals(t1rule1.amount_very_easy, 2)
        self.assertEquals(t1rule1.amount_easy, 2)
        self.assertEquals(t1rule1.amount_medium, 1)
        self.assertEquals(t1rule1.amount_hard, 0)
        self.assertEquals(t1rule1.amount_very_hard, 0)
        t1rule1.delete()

        t1rule2 = TrainingTemplateRule.objects.create(
            amount=2,
            training_template=template1,
            difficulty_profile_code=TrainingTemplateRule.MOSTLY_EASY,
            topic=self.topic_trigonometry,
        )
        self.assertEquals(t1rule2.amount_very_easy, 1)
        self.assertEquals(t1rule2.amount_easy, 1)
        self.assertEquals(t1rule2.amount_medium, 0)
        self.assertEquals(t1rule2.amount_hard, 0)
        self.assertEquals(t1rule2.amount_very_hard, 0)
        t1rule2.delete()

        t1rule3 = TrainingTemplateRule.objects.create(
            amount=1,
            training_template=template1,
            difficulty_profile_code=TrainingTemplateRule.MOSTLY_EASY,
            topic=self.topic_trigonometry,
        )
        self.assertEquals(t1rule3.amount_very_easy, 1)
        self.assertEquals(t1rule3.amount_easy, 0)
        self.assertEquals(t1rule3.amount_medium, 0)
        self.assertEquals(t1rule3.amount_hard, 0)
        self.assertEquals(t1rule3.amount_very_hard, 0)
        t1rule3.delete()

        t1rule4 = TrainingTemplateRule.objects.create(
            amount=9,
            training_template=template1,
            difficulty_profile_code=TrainingTemplateRule.MOSTLY_EASY,
            topic=self.topic_trigonometry,
        )
        self.assertEquals(t1rule4.amount_very_easy, 2)
        self.assertEquals(t1rule4.amount_easy, 3)
        self.assertEquals(t1rule4.amount_medium, 3)
        self.assertEquals(t1rule4.amount_hard, 1)
        self.assertEquals(t1rule4.amount_very_hard, 0)
        t1rule4.delete()

    def test_mostly_hard_profile(self):
        template1 = TrainingTemplate.objects.create(
            name="template1",
            course=self.math_course,
        )

        t1rule1 = TrainingTemplateRule.objects.create(
            amount=5,
            training_template=template1,
            difficulty_profile_code=TrainingTemplateRule.MOSTLY_HARD,
            topic=self.topic_trigonometry,
        )
        self.assertEquals(t1rule1.amount_very_easy, 0)
        self.assertEquals(t1rule1.amount_easy, 0)
        self.assertEquals(t1rule1.amount_medium, 1)
        self.assertEquals(t1rule1.amount_hard, 2)
        self.assertEquals(t1rule1.amount_very_hard, 2)
        t1rule1.delete()

        t1rule2 = TrainingTemplateRule.objects.create(
            amount=2,
            training_template=template1,
            difficulty_profile_code=TrainingTemplateRule.MOSTLY_HARD,
            topic=self.topic_trigonometry,
        )
        self.assertEquals(t1rule2.amount_very_easy, 0)
        self.assertEquals(t1rule2.amount_easy, 0)
        self.assertEquals(t1rule2.amount_medium, 0)
        self.assertEquals(t1rule2.amount_hard, 1)
        self.assertEquals(t1rule2.amount_very_hard, 1)
        t1rule2.delete()

        t1rule3 = TrainingTemplateRule.objects.create(
            amount=1,
            training_template=template1,
            difficulty_profile_code=TrainingTemplateRule.MOSTLY_HARD,
            topic=self.topic_trigonometry,
        )
        self.assertEquals(t1rule3.amount_very_easy, 0)
        self.assertEquals(t1rule3.amount_easy, 0)
        self.assertEquals(t1rule3.amount_medium, 0)
        self.assertEquals(t1rule3.amount_hard, 0)
        self.assertEquals(t1rule3.amount_very_hard, 1)
        t1rule3.delete()

        t1rule4 = TrainingTemplateRule.objects.create(
            amount=9,
            training_template=template1,
            difficulty_profile_code=TrainingTemplateRule.MOSTLY_HARD,
            topic=self.topic_trigonometry,
        )
        self.assertEquals(t1rule4.amount_very_easy, 0)
        self.assertEquals(t1rule4.amount_easy, 1)
        self.assertEquals(t1rule4.amount_medium, 3)
        self.assertEquals(t1rule4.amount_hard, 3)
        self.assertEquals(t1rule4.amount_very_hard, 2)
        t1rule4.delete()
