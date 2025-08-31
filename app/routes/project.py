from flask import Blueprint, render_template, request, jsonify, current_app, flash, redirect, url_for
from app.models.client import ClientRequest, db, Client
from app.models.project import create_project_from_request, Project, ProjectStage
from app.models.user import User
from datetime import datetime
import logging
from flask_login import login_required, current_user

project_bp = Blueprint('project', __name__, url_prefix='/projects')
logger = logging.getLogger(__name__)

@project_bp.route('/', methods=['GET'])
def list_projects():
    """Отображает список проектов"""
    projects = Project.query.all()
    return render_template('projects/list.html', projects=projects)

@project_bp.route('/<int:project_id>', methods=['GET'])
def view_project(project_id):
    """Отображает детали проекта"""
    project = Project.query.get_or_404(project_id)
    stages = ProjectStage.query.filter_by(project_id=project_id).order_by(ProjectStage.order_number).all()
    return render_template('projects/detail.html', project=project, stages=stages)

@project_bp.route('/new', methods=['GET', 'POST'])
@login_required
def create_project():
    """Создает новый проект"""
    if request.method == 'POST':
        try:
            data = request.form
            project = Project(
                name=data.get('name'),
                user_id=current_user.id,
                description=data.get('description')
            )
            
            if data.get('deadline'):
                project.deadline = datetime.strptime(data.get('deadline'), '%Y-%m-%d')
            
            db.session.add(project)
            db.session.flush()
            
            # Добавляем стандартные стадии, если указано
            if data.get('add_default_stages') == 'true':
                stages = [
                    {"name": "Анализ требований", "description": "Детальный разбор ТЗ, уточнение требований", "order": 1},
                    {"name": "Проектирование", "description": "Разработка архитектуры и дизайна", "order": 2},
                    {"name": "Разработка", "description": "Написание кода, создание функционала", "order": 3},
                    {"name": "Тестирование", "description": "Проверка работоспособности, поиск ошибок", "order": 4},
                    {"name": "Развертывание", "description": "Публикация проекта", "order": 5}
                ]
                
                for stage in stages:
                    db.session.add(ProjectStage(
                        project_id=project.id,
                        name=stage["name"],
                        description=stage["description"],
                        order_number=stage["order"]
                    ))
            
            db.session.commit()
            return jsonify({"success": True, "message": "Проект создан", "project_id": project.id})
        except Exception as e:
            db.session.rollback()
            logger.error(f"Ошибка при создании проекта: {e}")
            return jsonify({"success": False, "message": f"Ошибка: {str(e)}"}), 500
    
    # Для GET запроса показываем форму создания
    from app.models.client import Client
    clients = Client.query.all()
    # Получаем ТЗ без связанных проектов
    unassigned_requests = ClientRequest.query.filter(
        ~ClientRequest.id.in_(db.session.query(Project.request_id).filter(Project.request_id.isnot(None)))
    ).all()
    
    return render_template('projects/create.html', clients=clients, requests=unassigned_requests)

@project_bp.route('/<int:project_id>/update', methods=['POST'])
def update_project(project_id):
    """Обновляет информацию о проекте"""
    try:
        project = Project.query.get_or_404(project_id)
        data = request.form
        
        project.name = data.get('name', project.name)
        project.description = data.get('description', project.description)
        project.status = data.get('status', project.status)
        
        if data.get('client_id'):
            project.client_id = int(data.get('client_id'))
        
        if data.get('deadline'):
            project.deadline = datetime.strptime(data.get('deadline'), '%Y-%m-%d')
        
        project.updated_at = datetime.utcnow()
        
        db.session.commit()
        return jsonify({"success": True, "message": "Проект обновлен"})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Ошибка при обновлении проекта: {e}")
        return jsonify({"success": False, "message": f"Ошибка: {str(e)}"}), 500

@project_bp.route('/<int:project_id>/stages', methods=['POST'])
def add_stage(project_id):
    """Добавляет новую стадию к проекту"""
    try:
        data = request.form
        stage = ProjectStage(
            project_id=project_id,
            name=data.get('name'),
            description=data.get('description'),
            order_number=int(data.get('order_number', 1))
        )
        
        db.session.add(stage)
        db.session.commit()
        return jsonify({"success": True, "message": "Стадия добавлена", "stage_id": stage.id})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Ошибка при добавлении стадии: {e}")
        return jsonify({"success": False, "message": f"Ошибка: {str(e)}"}), 500

@project_bp.route('/stages/<int:stage_id>/update', methods=['POST'])
def update_stage(stage_id):
    """Обновляет информацию о стадии проекта"""
    try:
        stage = ProjectStage.query.get_or_404(stage_id)
        data = request.form
        
        stage.name = data.get('name', stage.name)
        stage.description = data.get('description', stage.description)
        stage.status = data.get('status', stage.status)
        stage.order_number = int(data.get('order_number', stage.order_number))
        
        if data.get('start_date'):
            stage.start_date = datetime.strptime(data.get('start_date'), '%Y-%m-%d')
        
        if data.get('end_date'):
            stage.end_date = datetime.strptime(data.get('end_date'), '%Y-%m-%d')
        
        stage.updated_at = datetime.utcnow()
        
        db.session.commit()
        return jsonify({"success": True, "message": "Стадия обновлена"})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Ошибка при обновлении стадии: {e}")
        return jsonify({"success": False, "message": f"Ошибка: {str(e)}"}), 500

@project_bp.route('/from_request/<int:request_id>', methods=['POST'])
def create_from_request(request_id):
    """Создает проект на основе существующего ТЗ"""
    try:
        client_request = ClientRequest.query.get_or_404(request_id)
        project = create_project_from_request(client_request)
        
        if project:
            return jsonify({
                "success": True, 
                "message": "Проект успешно создан", 
                "project_id": project.id
            })
        else:
            return jsonify({"success": False, "message": "Не удалось создать проект"}), 500
    except Exception as e:
        logger.error(f"Ошибка при создании проекта из ТЗ: {e}")
        return jsonify({"success": False, "message": f"Ошибка: {str(e)}"}), 500

@project_bp.route('/client/dashboard', methods=['GET'])
@login_required
def client_dashboard():
    """Личный кабинет пользователя - просмотр его проектов"""
    # Получаем проекты пользователя
    projects = Project.query.filter_by(user_id=current_user.id).order_by(Project.created_at.desc()).all()
    
    return render_template('projects/client_dashboard.html', projects=projects, user=current_user)

@project_bp.route('/client/<int:project_id>', methods=['GET'])
@login_required
def client_project_detail(project_id):
    """Детальный просмотр проекта пользователем"""
    # Получаем проект и проверяем, что он принадлежит пользователю
    project = Project.query.filter_by(id=project_id, user_id=current_user.id).first()
    if not project:
        flash('Проект не найден или у вас нет доступа к нему.', 'error')
        return redirect(url_for('project.client_dashboard'))
    
    # Получаем стадии проекта
    stages = ProjectStage.query.filter_by(project_id=project_id).order_by(ProjectStage.order_number).all()
    
    return render_template('projects/client_project_detail.html', project=project, stages=stages)
