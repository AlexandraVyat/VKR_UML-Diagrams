from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from math import isclose
from typing import Optional, Union


# Уровни сложности заданий
class DifficultyLevel(Enum):
    INITIAL = "Начальный"
    MEDIUM = "Средний"
    ADVANCED = "Продвинутый"


# Базовый класс пользователя
@dataclass
class User:
    id: int
    name: str
    login: str
    passwordHash: str


# Учитель
@dataclass
class Teacher(User):
    def createTask(self, task_id: int, title: str,
                   description: str,
                   difficulty: DifficultyLevel) -> "Task":
        return Task(task_id, title, description, difficulty)

    def editTask(self, task: "Task", title: str,
                 description: str) -> None:
        task.title = title
        task.description = description

    def deleteTask(self, task: "Task") -> None:
        task.exercises.clear()

    def assignTask(
        self,
        assignment_id: int,
        task: "Task",
        student: Optional["Student"] = None,
        group: Optional["StudentGroup"] = None,
        due_date: Optional[datetime] = None
    ) -> "TaskAssignment":
        return TaskAssignment(
            id=assignment_id,
            task=task,
            teacher=self,
            student=student,
            group=group,
            dueDate=due_date
        )

    def viewResults(self, results: list["Result"]) -> list["Result"]:
        return results

    def viewAnalytics(self, results: list["Result"]) -> dict:
        if not results:
            return {"Количество результатов": 0,
                    "Средний процент": 0}

        average = sum(r.percentage for r in results) / len(results)

        return {
            "Количество результатов": len(results),
            "Средний процент": round(average, 2)
        }


# Ученик
@dataclass
class Student(User):
    currentDifficulty: DifficultyLevel = DifficultyLevel.INITIAL

    def viewAssignments(
        self, assignments: list["TaskAssignment"]
    ) -> list["TaskAssignment"]:
        return [
            assignment for assignment in assignments
            if assignment.student == self
            or (
                assignment.group is not None
                and self in assignment.group.students
            )
        ]

    def submitAnswer(
        self,
        answer_id: int,
        exercise: "Exercise",
        value: float,
        result: "Result"
    ) -> "Answer":
        answer = Answer(
            id=answer_id,
            value=value,
            isCorrect=isclose(
                value, exercise.correctAnswer, rel_tol=1e-9
            ),
            submittedAt=datetime.now(),
            exercise=exercise
        )
        result.answers.append(answer)
        return answer

    def viewResult(self, result: "Result") -> "Result":
        return result


# Группа учеников
@dataclass
class StudentGroup:
    id: int
    name: str
    students: list[Student] = field(default_factory=list)


# Задание
@dataclass
class Task:
    id: int
    title: str
    description: str
    difficulty: DifficultyLevel
    exercises: list["Exercise"] = field(default_factory=list)

    def addExercise(self, exercise: "Exercise") -> None:
        self.exercises.append(exercise)

    def editExercise(
        self, exercise_id: int, expression: str,
        correct_answer: float
    ) -> None:
        for exercise in self.exercises:
            if exercise.id == exercise_id:
                exercise.expression = expression
                exercise.correctAnswer = correct_answer
                return

        raise ValueError("Упражнение не найдено")


# Отдельное упражнение внутри задания
@dataclass
class Exercise:
    id: int
    expression: str
    correctAnswer: float
    position: int


# Назначение задания
@dataclass
class TaskAssignment:
    id: int
    task: Task
    teacher: Teacher
    student: Optional[Student] = None
    group: Optional[StudentGroup] = None
    assignedAt: datetime = field(default_factory=datetime.now)
    dueDate: Optional[datetime] = None
    status: str = "Назначено"

    def __post_init__(self):
        # Задание назначается либо ученику, либо группе
        if (self.student is None) == (self.group is None):
            raise ValueError(
                "Необходимо указать либо ученика, либо группу"
            )


# Ответ ученика на упражнение
@dataclass
class Answer:
    id: int
    value: float
    isCorrect: bool
    submittedAt: datetime
    exercise: Exercise


# Результат выполнения задания
@dataclass
class Result:
    id: int
    student: Student
    assignment: TaskAssignment
    answers: list[Answer] = field(default_factory=list)
    correctCount: int = 0
    totalExercises: int = 0
    percentage: float = 0.0
    completedAt: Optional[datetime] = None

    def calculatePercentage(self) -> float:
        self.totalExercises = len(self.assignment.task.exercises)
        self.correctCount = sum(
            1 for answer in self.answers if answer.isCorrect
        )

        if self.totalExercises == 0:
            self.percentage = 0.0
        else:
            self.percentage = (
                self.correctCount / self.totalExercises
            ) * 100

        self.completedAt = datetime.now()
        return self.percentage


# Определение сложности следующего задания
def adaptDifficulty(
    student: Student, result: Result
) -> DifficultyLevel:

    levels = list(DifficultyLevel)
    current_index = levels.index(student.currentDifficulty)

    if result.percentage >= 80:
        current_index = min(current_index + 1, len(levels) - 1)
    elif result.percentage < 50:
        current_index = max(current_index - 1, 0)

    student.currentDifficulty = levels[current_index]
    return student.currentDifficulty
