from database.enums import ProficiencyLevel

GRADE_TO_LEVEL: dict[int, ProficiencyLevel] = {
    1: ProficiencyLevel.BEGINNER,
    2: ProficiencyLevel.BEGINNER,
    3: ProficiencyLevel.ELEMENTARY,
    4: ProficiencyLevel.ELEMENTARY,
    5: ProficiencyLevel.INTERMEDIATE,
    6: ProficiencyLevel.INTERMEDIATE,
    7: ProficiencyLevel.UPPER_INTERMEDIATE,
    8: ProficiencyLevel.UPPER_INTERMEDIATE,
    9: ProficiencyLevel.UPPER_INTERMEDIATE,
    10: ProficiencyLevel.ADVANCED,
    11: ProficiencyLevel.ADVANCED,
}

LEVEL_TO_GRADES: dict[ProficiencyLevel, list[int]] = {
    ProficiencyLevel.BEGINNER: [1, 2],
    ProficiencyLevel.ELEMENTARY: [3, 4],
    ProficiencyLevel.INTERMEDIATE: [5, 6],
    ProficiencyLevel.UPPER_INTERMEDIATE: [7, 8, 9],
    ProficiencyLevel.ADVANCED: [10, 11],
    ProficiencyLevel.NATIVE: [11],
}
