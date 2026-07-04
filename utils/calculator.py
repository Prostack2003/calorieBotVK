def calculate_norm(gender, age, height, weight, activity, goal):
    """Расчёт суточной нормы КБЖУ по формуле Миффлина-Сан Жеора"""
    if gender == 'male':
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    else:
        bmr = 10 * weight + 6.25 * height - 5 * age - 161
    
    tdee = bmr * activity
    
    if goal == 'lose':
        tdee *= 0.8
    elif goal == 'gain':
        tdee *= 1.15
    
    proteins = weight * 2
    fats = weight * 1
    carbs = (tdee - (proteins * 4) - (fats * 9)) / 4
    
    return {
        'calories': round(tdee),
        'proteins': round(proteins, 1),
        'fats': round(fats, 1),
        'carbs': round(carbs, 1)
    }