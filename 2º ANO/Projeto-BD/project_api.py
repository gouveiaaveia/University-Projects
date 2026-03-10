import flask
import logging
import psycopg2
import time
import random
from datetime import datetime, timedelta, timezone
import jwt
from dotenv import load_dotenv
import os
from functools import wraps

app = flask.Flask(__name__)
app.config['JWT_SECRET_KEY'] = 'some_jwt_secret_key'

StatusCodes = {
    'success': 200,
    'api_error': 400,
    'internal_error': 500,
    'unauthorized': 401
}

##########################################################
## DATABASE ACCESS
##########################################################

load_dotenv()
SECRET_KEY = os.getenv("JWT_SECRET")

def db_connection():
    db = psycopg2.connect(
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT'),
        database=os.getenv('DB_NAME')
    )

    return db

##########################################################
## AUTHENTICATION HELPERS
##########################################################

def check_token(token, type):
    try:

        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])

        logger.info(f"Decoded payload: {payload}")
        user_id = payload.get('user_id')

        if user_id is None:
            return None
        
        conn = db_connection()
        cur = conn.cursor()

        if type == 'student':
            cur.execute("""
                SELECT person_id FROM student WHERE person_id = %s
            """, (user_id,))
        elif type == 'staff':
            cur.execute("""
                SELECT person_id FROM administrative_staff WHERE person_id = %s
            """, (user_id,))
        elif type == 'instructor':
            cur.execute("""
                SELECT professor_person_id FROM coordinator_instructor WHERE professor_person_id = %s
            """, (user_id,))

        if cur.fetchone() is None:
            logger.info("User not found in the database")
            return None
        else:
            return user_id
    except jwt.ExpiredSignatureError:
        logger.error("Token has expired")
        return None
    except jwt.InvalidTokenError:
        logger.error("Invalid token")
        return None

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = flask.request.headers.get('Authorization')
        
        logger.info(f'token1: {token}')

        if not token:
            return flask.jsonify({'status': StatusCodes['unauthorized'], 'errors': 'Token is missing!', 'results': None})

        return f(*args, **kwargs)
    return decorated


def create_person(data):
    try:
        username = data.get('username')
        cc = data.get('cc')
        age = data.get('age')
        district = data.get('district')
        email = data.get('email')
        password = data.get('password')

        # Verificar se todos os campos obrigatórios estão presentes
        if not username or not email or not password or not cc or not age or not district:
            return flask.jsonify({
                'status': StatusCodes['api_error'],
                'errors': 'Username, email, password, cc, age and district are required',
                'results': None
            })

        conn = db_connection()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO person (name, cc, age, district, email, password) 
            VALUES (%s, %s, %s, %s, %s, crypt(%s, gen_salt('bf')))
            RETURNING id
        """, (username, cc, age, district, email, password))

        person_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()

        logger.info(f"Person created with ID: {person_id}")

        return person_id

    except Exception as e:
        logger.error(f"Error creating person: {e}")
        return None

##########################################################
## ENDPOINTS
##########################################################

@app.route('/dbproj/user', methods=['PUT'])
def login_user():
    try:
        data = flask.request.get_json()
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return flask.jsonify({
                'status': StatusCodes['api_error'],
                'errors': 'Username and password are required',
                'results': None
            })

        conn = db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT id FROM person 
            WHERE name = %s AND password = crypt(%s, password)
        """, (username, password))

        result = cur.fetchone()
        cur.close()
        conn.close()

        if result is None:
            return flask.jsonify({
                'status': StatusCodes['unauthorized'],
                'errors': 'Invalid credentials',
                'results': None
            })

        user_id = result[0]

        # Time to expiration
        expiration = datetime.now(timezone.utc) + timedelta(minutes=60)
        payload = {
            'user_id': user_id,
            'exp': expiration
        }

        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
        if isinstance(token, bytes):
            token = token.decode('utf-8')
        
        logger.info(f"Token generated: {token}")

        return flask.jsonify({
            'status': StatusCodes['success'],
            'errors': None,
            'results': token
        })

    except Exception as e:
        return flask.jsonify({
            'status': StatusCodes['internal_error'],
            'errors': str(e),
            'results': None
        })

@app.route('/dbproj/register/student', methods=['POST'])
@token_required
def register_student():
    # Verificar se o token é válido e se o usuário é do tipo 'staff'
    token = flask.request.headers.get('Authorization')

    if check_token(token, 'staff') is None:
        return flask.jsonify({
            'status': StatusCodes['unauthorized'],
            'errors': 'Only staff members can add students',
            'results': None
        })

    # Obter os dados do corpo da requisição
    data = flask.request.get_json()

    student_number = data.get('student_number')
    account_value = data.get('account_value')

    if not student_number or not account_value:
        return flask.jsonify({
            'status': StatusCodes['api_error'],
            'errors': 'Student number and account value are required',
            'results': None
        })
    

    # Criar a pessoa no banco de dados
    resultUserId = create_person(data)
    if resultUserId is None:
        return flask.jsonify({
            'status': StatusCodes['internal_error'],
            'errors': 'Failed to create person',
            'results': None
        })

    try:
        
        # Inserir o estudante no banco de dados
        conn = db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO student (student_number, account_value, person_id) 
            VALUES (%s, %s, %s)
        """, (student_number, account_value, resultUserId))
        conn.commit()
        cur.close()
        conn.close()

        logger.info(f"Student created with ID: {resultUserId}")

    except Exception as e:
        logger.error(f"Error creating student: {e}")
        return flask.jsonify({
            'status': StatusCodes['internal_error'],
            'errors': str(e),
            'results': None
        })

    # Retornar a resposta de sucesso
    response = {
        'status': StatusCodes['success'],
        'errors': None,
        'results': resultUserId,
        'student_number': student_number
    }
    return flask.jsonify(response)


@app.route('/dbproj/register/staff', methods=['POST'])
@token_required
def register_staff():
    # Verificar se o token é válido e se o usuário é do tipo 'staff'
    token = flask.request.headers.get('Authorization')

    if check_token(token, 'staff') is None:
        return flask.jsonify({
            'status': StatusCodes['unauthorized'],
            'errors': 'Only staff members can add staff',
            'results': None
        })

    # Obter os dados do corpo da requisição
    data = flask.request.get_json()

    staff_number = data.get('staff_number')

    if not staff_number:
        return flask.jsonify({
            'status': StatusCodes['api_error'],
            'errors': 'Staff number is required',
            'results': None
        })

    # Criar a pessoa no banco de dados
    resultUserId = create_person(data)
    if resultUserId is None:
        return flask.jsonify({
            'status': StatusCodes['internal_error'],
            'errors': 'Failed to create person',
            'results': None
        })

    try:
        # Inserir o estudante no banco de dados
        conn = db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO administrative_staff (staff_number, person_id) 
            VALUES (%s, %s)
        """, (staff_number, resultUserId))
        conn.commit()
        cur.close()
        conn.close()

        logger.info(f"Staff created with ID and Staff Number: {resultUserId , staff_number}")

    except Exception as e:
        logger.error(f"Error creating student: {e}")
        return flask.jsonify({
            'status': StatusCodes['internal_error'],
            'errors': str(e),
            'results': None
        })

    # Retornar a resposta de sucesso
    response = {
        'status': StatusCodes['success'],
        'errors': None,
        'results': resultUserId,
        'staff_number': staff_number
    }
    return flask.jsonify(response)


@app.route('/dbproj/register/instructor', methods=['POST'])
@token_required
def register_instructor():
    
    token = flask.request.headers.get('Authorization')
    if check_token(token, 'staff') is None:
        return flask.jsonify({
            'status': StatusCodes['unauthorized'],
            'errors': 'Only staff members can add students',
            'results': None
        })
    

    data = flask.request.get_json()

    type = data.get('type')
    instructor_number = data.get('instructor_number')

    if not type or not instructor_number:
        return flask.jsonify({
            'status': StatusCodes['api_error'],
            'errors': 'Type and instructor number are required',
            'results': None
        })

    resultUserId = create_person(data)
    if resultUserId is None:
        return flask.jsonify({
            'status': StatusCodes['internal_error'],
            'errors': 'Failed to create person',
            'results': None
        })
    
    try:
        conn = db_connection()
        cur = conn.cursor()

        if type not in ['coordenador', 'assistente']:
            cur.close()
            conn.close()
            return flask.jsonify({
                'status': StatusCodes['api_error'],
                'errors': 'Type must be either "coordenador" or "assistente"',
                'results': None
            })
        
        if type == 'coordenador':
            cur.execute("""
            INSERT INTO coordinator_instructor (coordinator_number, professor_person_id) 
            VALUES (%s, %s)
            """, (instructor_number, resultUserId))
            conn.commit()
            cur.close()
            conn.close()
        
        if type == 'assistente':
            cur.execute("""
            INSERT INTO assistent_instructor (assistent_number, professor_person_id) 
            VALUES (%s, %s)
            """, (instructor_number, resultUserId))
            conn.commit()
            cur.close()
            conn.close()

        logger.info(f"Instructor created with ID: {resultUserId}")

    except Exception as e:
        logger.error(f"Error creating instructor: {e}")
        return flask.jsonify({
            'status': StatusCodes['internal_error'],
            'errors': str(e),
            'results': None
        })
    
    # Retornar a resposta de sucesso
    response = {
        'status': StatusCodes['success'],
        'errors': None,
        'results': resultUserId,
        'Instructor Number': instructor_number
    }
    return flask.jsonify(response)
    


@app.route('/dbproj/enroll_degree/<degree_id>', methods=['POST'])
@token_required
def enroll_degree(degree_id):
    
    token = flask.request.headers.get('Authorization')
    if check_token(token, 'staff') is None:
        return flask.jsonify({
            'status': StatusCodes['unauthorized'],
            'errors': 'Only staff can enroll students',
            'results': None
        })
    

    data = flask.request.get_json()

    student_id = data.get('student_id')
    date = data.get('date')

    if not student_id or not date:
        return flask.jsonify({'status': StatusCodes['api_error'], 'errors': 'Student ID and date are required', 'results': None})
    

    try:
        conn = db_connection()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO student_degree (student_person_id, degree_id, enrollement_date, active) 
            VALUES (%s, %s, %s, true)
            """,(student_id, degree_id, date))
        conn.commit()
        cur.close()
        conn.close()

        logger.info(f"Student enrolled in degree successfully")
    
    except Exception as e:
        logger.error(f"Error enrolling in degree: {e}")
        return flask.jsonify({
            'status': StatusCodes['internal_error'],
            'errors': str(e),
            'results': None
        })
    
    response = {'status': StatusCodes['success'], 'errors': None}
    return flask.jsonify(response)



@app.route('/dbproj/enroll_activity/<activity_id>', methods=['POST'])
@token_required
def enroll_activity(activity_id):

    token = flask.request.headers.get('Authorization')

    student_id = check_token(token, 'student')

    if student_id is None:
        return flask.jsonify({
            'status': StatusCodes['unauthorized'],
            'errors': 'Only staff members can add students',
            'results': None
        })
    
    try:

        conn = db_connection()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO student_extracurricular_activities (student_person_id, extracurricular_activities_id) 
            VALUES (%s, %s)
            """,(student_id, activity_id))
        conn.commit()
        cur.close()
        conn.close()

        logger.info(f"Student enrolled succefully")
     
    except Exception as e:
        logger.error(f"Error enrrolling: {e}")
        return flask.jsonify({
            'status': StatusCodes['internal_error'],
            'errors': str(e),
            'results': None
        })
    
    response = {
        'status': StatusCodes['success'],
        'errors': None,
        'results': (student_id, activity_id)
    }
    return flask.jsonify(response)


@app.route('/dbproj/enroll_course_edition/<course_edition_id>', methods=['POST'])
@token_required
def enroll_course_edition(course_edition_id):

    token = flask.request.headers.get('Authorization')
    student_id = check_token(token, 'student')
    if student_id is None:
        return flask.jsonify({
            'status': StatusCodes['unauthorized'],
            'errors': 'Only students can enroll in course editions',
            'results': None
        })
    

    if course_edition_id is None:
        return flask.jsonify({'status': StatusCodes['api_error'], 'errors': 'Course edition ID is required', 'results': None})
    
    data = flask.request.get_json()
    classes = data.get('classes', [])

    if not classes:
        return flask.jsonify({'status': StatusCodes['api_error'], 'errors': 'At least one class ID is required', 'results': None})
    
    try:

        conn = db_connection()
        cur = conn.cursor()

        for class_id in classes:
            cur.execute("""
                        INSERT INTO student_class (student_person_id, class_class_number)
                        SELECT %s, %s
                        FROM
                            course_edition ce
                        WHERE
                            ce.id = %s
                            AND COALESCE(ce.enrolled_count, 0) < ce.capacity
                            AND EXISTS (
                                SELECT 1
                                FROM
                                    student_degree sd
                                JOIN
                                    degree_course dc ON sd.degree_id = dc.degree_id 
                                WHERE
                                    sd.student_person_id = %s
                                    AND sd.active = TRUE                           
                                    AND dc.course_course_code = ce.course_course_code
                            );""", (student_id, class_id, course_edition_id, student_id))

            logger.info(f"Student enrolled in course edition successfully")

        conn.commit()
        cur.close()
        conn.close()
    
    except Exception as e:
        logger.error(f"Error enrolling in course edition: {e}")
        return flask.jsonify({
            'status': StatusCodes['internal_error'],
            'errors': str(e),
            'results': None
        })
    
    response = {'status': StatusCodes['success'], 'errors': None}
    return flask.jsonify(response)


@app.route('/dbproj/submit_grades/<course_edition_id>', methods=['POST'])
@token_required
def submit_grades(course_edition_id):

    token = flask.request.headers.get('Authorization')
    instructor_id = check_token(token, 'instructor')
    if instructor_id is None:
        return flask.jsonify({
            'status': StatusCodes['unauthorized'],
            'errors': 'Only Coordinator Instructors can submit grades',
            'results': None
        })
    
    if course_edition_id is None:
        return flask.jsonify({'status': StatusCodes['api_error'], 'errors': 'Course edition ID is required', 'results': None})
    
    try:
        conn = db_connection()
        cur = conn.cursor()

        cur.execute(""" 
                    SELECT coordinator_instructor_professor_person_id, course_course_code, edition_id
                    FROM course_edition
                    WHERE id = %s
                    FOR UPDATE;
                    """, (course_edition_id,))
        
        result = cur.fetchall()
        cur.close()
        conn.close()

        if not result:
            return flask.jsonify({'status': StatusCodes['api_error'], 'errors': 'Course edition not found', 'results': None})

        coordinator_instructor_id = result[0][0]
        course_code = result[0][1]
        edition_id = result[0][2]

        if coordinator_instructor_id != instructor_id:
            return flask.jsonify({'status': StatusCodes['unauthorized'], 'errors': 'Only Coordinator Instructors of the course can submit grades', 'results': None})
    
    except Exception as e:
        logger.error(f"Error fetching course edition: {e}")
        return flask.jsonify({
            'status': StatusCodes['internal_error'],
            'errors': str(e),
            'results': None
        })

    data = flask.request.get_json()
    year = data.get('year')
    semestre = data.get('semestre')
    grades = data.get('grades', [])
    period_type = data.get('period_type')
    date = data.get('date')

    if not grades or not year or not semestre or not period_type or not date:
        logger.error(f"Missing required fields: {grades}, {year}, {semestre}, {period_type}")
        return flask.jsonify({'status': StatusCodes['api_error'], 'errors': 'Period, year, semestre, date and grades are required', 'results': None})
    
    try:
        conn = db_connection()
        cur = conn.cursor()

        for grade in grades:
            student_id = grade.get('student_id')
            grade_value = grade.get('grade')

            if not student_id or not grade_value:
                return flask.jsonify({'status': StatusCodes['api_error'], 'errors': 'Student ID and grade are required', 'results': None})

            cur.execute("""
                BEGIN;
                SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;
                INSERT INTO grade
                VALUES (
                    %s, %s, 
                    (SELECT id FROM period WHERE type = %s AND semestre = %s AND DATE_PART('year', period_date_start) = %s),
                    %s, %s, %s
                )
                """, (grade_value, date, period_type, semestre, year, student_id, edition_id, course_code))
        
        conn.commit()
        cur.close()
        conn.close()

        logger.info(f"Grades submitted successfully")

    except Exception as e:
        logger.error(f"Error submitting grades: {e}")
        return flask.jsonify({
            'status': StatusCodes['internal_error'],
            'errors': str(e),
            'results': None
        })
    
    response = {'status': StatusCodes['success'], 'errors': None}
    return flask.jsonify(response)


@app.route('/dbproj/student_details/<student_id>', methods=['GET'])
@token_required
def student_details(student_id):

    token = flask.request.headers.get('Authorization')
    if check_token(token, 'staff') is None:
        return flask.jsonify({
            'status': StatusCodes['unauthorized'],
            'errors': 'Only staff members can access student details',
            'results': None
        })

    try:

        conn = db_connection()
        cur = conn.cursor()

        cur.execute("BEGIN;")
        cur.execute("SET TRANSACTION ISOLATION LEVEL READ COMMITTED;")

        cur.execute("""SELECT 
                        JSON_BUILD_OBJECT(
                        'course_name', c.course_name,
						'course_edition_id', ce.id,
                        'year', e.edition_year,
                        'avarage', ROUND(AVG(g.grade), 2)
						)
                        FROM student_degree AS sd
                        JOIN degree_course AS dc ON dc.degree_id = sd.degree_id 
                        JOIN course AS c ON dc.course_course_code = c.course_code
                        JOIN course_edition AS ce ON dc.course_course_code = ce.course_course_code
                        JOIN edition AS e ON ce.edition_id = e.id
                        JOIN grade AS g ON 
                        g.student_person_id = sd.student_person_id AND 
                        g.course_edition_edition_id = ce.edition_id AND 
                        g.course_edition_course_course_code = ce.course_course_code
                        WHERE sd.student_person_id = %s AND sd.active IS TRUE
                        GROUP BY ce.id, c.course_name, e.edition_year;
                        """, (student_id,))
        
        resultStudentDetails = cur.fetchall()
        conn.commit()
        cur.close()
        conn.close()

    except Exception as e:
        logger.error(f"Error fetching student details: {e}")
        return flask.jsonify({
            'status': StatusCodes['internal_error'],
            'errors': str(e),
            'results': None
        })

    response = {'status': StatusCodes['success'], 'errors': None, 'results': resultStudentDetails}
    return flask.jsonify(response)


@app.route('/dbproj/degree_details/<degree_id>', methods=['GET'])
@token_required
def degree_details(degree_id):

    token = flask.request.headers.get('Authorization')
    if check_token(token, 'staff') is None:
        return flask.jsonify({
            'status': StatusCodes['unauthorized'],
            'errors': 'Only staff members can use this endpoint',
            'results': None
        })
    
    if degree_id is None:
        return flask.jsonify({'status': StatusCodes['api_error'], 'errors': 'Degree ID is required', 'results': None})
    
    try:
        conn = db_connection()
        cur = conn.cursor()

        cur.execute("BEGIN;")
        cur.execute("SET TRANSACTION ISOLATION LEVEL READ COMMITTED;")

        cur.execute("""SELECT 
                        JSON_AGG(
                            JSON_BUILD_OBJECT(
                                'course_code', c.course_code, 
                                'course_name', c.course_name, 
                                'edition_id', e.id, 
                                'edition_year', e.edition_year, 
                                'capacity', ce.capacity, 
                                'enrolled_count', (
                                    SELECT COUNT(DISTINCT sc.student_person_id)
                                    FROM timetable t
                                    JOIN student_class sc ON sc.class_class_number = t.class_class_number
                                    WHERE t.course_edition_edition_id = ce.edition_id
                                    AND t.course_edition_course_course_code = ce.course_course_code
                                ), 
                                'approved_students', (
                                    SELECT COUNT(DISTINCT g.student_person_id)
                                    FROM grade g
                                    WHERE g.course_edition_edition_id = ce.edition_id
                                    AND g.course_edition_course_course_code = ce.course_course_code
                                    AND g.grade >= 10
                                ), 
                                'coordinator_number', ci.coordinator_number,
                                'assistents', (
                                    SELECT JSON_AGG(DISTINCT ai.professor_person_id)
                                    FROM assistent_instructor_course_edition aice
                                    JOIN assistent_instructor ai 
                                        ON aice.assistent_instructor_professor_person_id = ai.professor_person_id
                                    WHERE aice.course_edition_edition_id = ce.edition_id 
                                    AND aice.course_edition_course_course_code = ce.course_course_code
                                )
                            )
                        ) AS course_editions
                    FROM degree d
                    JOIN degree_course dc ON dc.degree_id = d.id
                    JOIN course c ON dc.course_course_code = c.course_code
                    JOIN course_edition ce ON c.course_code = ce.course_course_code
                    JOIN edition e ON ce.edition_id = e.id
                    JOIN coordinator_instructor ci ON ce.coordinator_instructor_professor_person_id = ci.professor_person_id
                    WHERE d.id = %s
                    AND e.edition_year = (
                        SELECT MAX(e2.edition_year)
                        FROM course_edition ce2
                        JOIN edition e2 ON ce2.edition_id = e2.id
                        WHERE ce2.course_course_code = c.course_code
                    )
                    GROUP BY c.course_code
                    ORDER BY c.course_code;

                    """, (degree_id,))
        
        resultDegreeDetails = cur.fetchall()
        conn.commit()
        cur.close()
        conn.close()

    except Exception as e:
        logger.error(f"Error fetching degree details: {e}")
        return flask.jsonify({
            'status': StatusCodes['internal_error'],
            'errors': str(e),
            'results': None
        })

    response = {'status': StatusCodes['success'], 'errors': None, 'results': resultDegreeDetails}
    return flask.jsonify(response)

@app.route('/dbproj/top3', methods=['GET'])
@token_required
def top3_students():

    token = flask.request.headers.get('Authorization')
    if check_token(token, 'staff') is None:
        return flask.jsonify({
            'status': StatusCodes['unauthorized'],
            'errors': 'Only staff members can add students',
            'results': None
        })
    
    try:

        conn = db_connection()
        cur = conn.cursor()

        cur.execute("BEGIN;")
        cur.execute("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;")

        cur.execute("""
                    SELECT
                        p.name AS nome,
                        ag.avg_grade AS média,
                        COALESCE(gt.grades, '[]') AS grades,
                        COALESCE(sa.activities, '[]') AS extracurricular_activities
                    FROM person p

                    JOIN (
                        SELECT
                            g.student_person_id,
                            ROUND(AVG(g.grade), 2) AS avg_grade
                        FROM grade g
                        WHERE DATE_PART('year', g.grade_date) = DATE_PART('year', CURRENT_DATE)
                        GROUP BY g.student_person_id
                    ) ag ON p.id = ag.student_person_id

                    LEFT JOIN (
                        SELECT
                            g.student_person_id,
                            JSON_AGG(
                                JSON_BUILD_OBJECT(
                                    'course_name', c.course_name,
                                    'course_id',   g.course_edition_edition_id,
                                    'date',        TO_CHAR(g.grade_date, 'YYYY-MM-DD'),
                                    'grade',       g.grade
                                )
                                ORDER BY g.grade_date
                            ) AS grades
                        FROM grade g
                        JOIN course c ON g.course_edition_course_course_code = c.course_code
                        WHERE DATE_PART('year', g.grade_date) = DATE_PART('year', CURRENT_DATE)
                        GROUP BY g.student_person_id
                    ) gt ON p.id = gt.student_person_id

                    LEFT JOIN (
                        SELECT
                            s.student_person_id,
                            JSON_AGG(s.extracurricular_activities_id ORDER BY s.extracurricular_activities_id) AS activities
                        FROM (
                            SELECT DISTINCT
                                student_person_id,
                                extracurricular_activities_id
                            FROM student_extracurricular_activities
                        ) s
                        GROUP BY s.student_person_id
                    ) sa ON p.id = sa.student_person_id

                    ORDER BY ag.avg_grade DESC
                    LIMIT 3;

                """)
        
        resultTop3 = cur.fetchall()
        conn.commit()
        cur.close()
        conn.close()

    except Exception as e:
        if conn:
            try:
                conn.rollback()
            except Exception as rb_e:
                logger.error(f"Error during rollback in top3_students: {rb_e}")
        logger.error(f"Error fetching top 3 students: {e}")
        return flask.jsonify({
            'status': StatusCodes['internal_error'],
            'errors': str(e),
            'results': None
        })

    response = {'status': StatusCodes['success'], 'errors': None, 'results': resultTop3}
    return flask.jsonify(response)

@app.route('/dbproj/top_by_district', methods=['GET'])
@token_required
def top_by_district():

    token = flask.request.headers.get('Authorization')

    if check_token(token, 'staff') is None:
        return flask.jsonify({
            'status': StatusCodes['unauthorized'],
            'errors': 'Only staff members can do this check',
            'results': None
        })

    try:
        conn = db_connection()
        cur = conn.cursor()

        cur.execute("BEGIN;")
        cur.execute("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;")

        cur.execute("""SELECT 
                            JSON_BUILD_OBJECT(
                                'district', p.district, 
                                'average', ag.avg_grade,
                                'student_id', p.id
                            )
                        FROM person p
                        JOIN student s ON s.person_id = p.id

                        JOIN (
                            SELECT 
                                g.student_person_id,
                                ROUND(AVG(g.grade), 2) AS avg_grade
                            FROM grade g
                            WHERE DATE_PART('year', g.grade_date) = DATE_PART('year', CURRENT_DATE)
                            GROUP BY g.student_person_id
                        ) ag ON ag.student_person_id = s.person_id

                        JOIN (
                            SELECT 
                                p2.district,
                                MAX(ag2.avg_grade) AS max_avg
                            FROM person p2
                            JOIN student s2 ON s2.person_id = p2.id
                            JOIN (
                                SELECT 
                                    g2.student_person_id,
                                    ROUND(AVG(g2.grade), 2) AS avg_grade
                                FROM grade g2
                                WHERE DATE_PART('year', g2.grade_date) = DATE_PART('year', CURRENT_DATE)
                                GROUP BY g2.student_person_id
                            ) ag2 ON ag2.student_person_id = s2.person_id
                            GROUP BY p2.district
                        ) max_district ON max_district.district = p.district AND ag.avg_grade = max_district.max_avg

                        ORDER BY p.district;

                    """)
    
        resultTopByDistrict = cur.fetchall()
        conn.commit()
        cur.close()
        conn.close()

    except Exception as e:
        if conn:
            try:
                conn.rollback()
            except Exception as rb_e:
                logger.error(f"Error during rollback in top_by_district: {rb_e}")
        logger.error(f"Error fetching top by district: {e}")
        return flask.jsonify({
            'status': StatusCodes['internal_error'],
            'errors': str(e),
            'results': None
        }), StatusCodes['internal_error']
    

    response = {'status': StatusCodes['success'], 'errors': None, 'results': resultTopByDistrict}
    return flask.jsonify(response)

@app.route('/dbproj/report', methods=['GET'])
@token_required
def monthly_report():

    token = flask.request.headers.get('Authorization')
    if check_token(token, 'staff') is None:
        return flask.jsonify({
            'status': StatusCodes['unauthorized'],
            'errors': 'Only staff members can do this check',
            'results': None
        })
    
    try:
        conn = db_connection()
        cur = conn.cursor()

        cur.execute("BEGIN;")
        cur.execute("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;")

        cur.execute("""SELECT JSON_BUILD_OBJECT(
                            'month', sub.month,
                            'course_edition_id', sub.edition_id,
                            'course_edition_name', sub.course_name,
                            'approved', sub.approved,
                            'evaluated', sub.evaluated
                        ) AS result
                        FROM (
                            SELECT DISTINCT ON (DATE_PART('year', g.grade_date), DATE_PART('month', g.grade_date))
                                DATE_PART('month', g.grade_date) AS month,
                                ce.edition_id,
                                c.course_name,
                                COUNT(CASE WHEN g.grade >= 10 THEN 1 END) AS approved,
                                COUNT(*) AS evaluated
                            FROM grade g
                            JOIN course_edition ce 
                                ON ce.course_course_code = g.course_edition_course_course_code
                                AND ce.edition_id = g.course_edition_edition_id
                            JOIN course c 
                                ON c.course_code = ce.course_course_code
                            WHERE g.grade_date >= (CURRENT_DATE - INTERVAL '12 months')
                            GROUP BY
                                DATE_PART('year', g.grade_date),
                                DATE_PART('month', g.grade_date),
                                ce.edition_id,
                                c.course_name
                            ORDER BY
                                DATE_PART('year', g.grade_date),
                                DATE_PART('month', g.grade_date),
                                COUNT(CASE WHEN g.grade >= 10 THEN 1 END) DESC
                        ) sub
                        ORDER BY sub.month;

                    """)
        
        resultReport = cur.fetchall()
        conn.commit()
        cur.close()
        conn.close()

    except Exception as e:
        if conn:
            try:
                conn.rollback()
            except Exception as rb_e:
                logger.error(f"Error during rollback in monthly_report: {rb_e}")
        logger.error(f"Error fetching monthly report: {e}")
        return flask.jsonify({
            'status': StatusCodes['internal_error'],
            'errors': str(e),
            'results': None
        })

    response = {'status': StatusCodes['success'], 'errors': None, 'results': resultReport}
    return flask.jsonify(response)

@app.route('/dbproj/delete_details/<student_id>', methods=['DELETE'])
@token_required
def delete_student(student_id):

    token = flask.request.headers.get('Authorization')
    if check_token(token, 'staff') is None:
        return flask.jsonify({
            'status': StatusCodes['unauthorized'],
            'errors': 'Only staff members can delete students',
            'results': None
        })
    
    if student_id is None:
        return flask.jsonify({'status': StatusCodes['api_error'], 'errors': 'Student ID is required', 'results': None})
    
    try:
        conn = db_connection()
        cur = conn.cursor()

        cur.execute("""DELETE FROM student WHERE person_id = %s""", (student_id,))
        conn.commit()
        cur.close()
        conn.close()

        logger.info(f"Student deleted successfully")


    except Exception as e:
        logger.error(f"Error deleting student: {e}")
        return flask.jsonify({
            'status': StatusCodes['internal_error'],
            'errors': str(e),
            'results': None
        })

    response = {'status': StatusCodes['success'], 'errors': None}
    return flask.jsonify(response)

if __name__ == '__main__':
    # set up logging
    logging.basicConfig(filename='log_file.log')
    logger = logging.getLogger('logger')
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    # create formatter
    formatter = logging.Formatter('%(asctime)s [%(levelname)s]:  %(message)s', '%H:%M:%S')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    host = '127.0.0.1'
    port = 8080
    app.run(host=host, debug=True, threaded=True, port=port)
    logger.info(f'API stubs online: http://{host}:{port}')