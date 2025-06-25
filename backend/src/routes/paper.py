from flask import Blueprint, request, jsonify
from src.models.user import db, Paper, Comment, Bookmark, Vote, User
import requests
from datetime import datetime
import re

paper_bp = Blueprint('paper', __name__)

def fetch_paper_from_doi(doi):
    """Fetch paper information from CrossRef API using DOI"""
    try:
        url = f"https://api.crossref.org/works/{doi}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()['message']
            
            # Extract authors
            authors = []
            if 'author' in data:
                for author in data['author']:
                    given = author.get('given', '')
                    family = author.get('family', '')
                    authors.append(f"{given} {family}".strip())
            
            # Extract published date
            published_date = None
            if 'published-print' in data and 'date-parts' in data['published-print']:
                date_parts = data['published-print']['date-parts'][0]
                if len(date_parts) >= 3:
                    published_date = datetime(date_parts[0], date_parts[1], date_parts[2]).date()
                elif len(date_parts) >= 1:
                    published_date = datetime(date_parts[0], 1, 1).date()
            
            return {
                'title': data.get('title', [''])[0],
                'authors': ', '.join(authors),
                'abstract': data.get('abstract', ''),
                'published_date': published_date,
                'journal': data.get('container-title', [''])[0] if data.get('container-title') else ''
            }
    except Exception as e:
        print(f"Error fetching DOI {doi}: {e}")
    return None

def fetch_paper_from_arxiv(arxiv_id):
    """Fetch paper information from arXiv API"""
    try:
        # Clean arxiv_id (remove version if present)
        clean_id = re.sub(r'v\d+$', '', arxiv_id)
        url = f"http://export.arxiv.org/api/query?id_list={clean_id}"
        response = requests.get(url)
        
        if response.status_code == 200:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.content)
            
            # Find the entry
            entry = root.find('{http://www.w3.org/2005/Atom}entry')
            if entry is not None:
                title = entry.find('{http://www.w3.org/2005/Atom}title').text.strip()
                summary = entry.find('{http://www.w3.org/2005/Atom}summary').text.strip()
                
                # Extract authors
                authors = []
                for author in entry.findall('{http://www.w3.org/2005/Atom}author'):
                    name = author.find('{http://www.w3.org/2005/Atom}name').text
                    authors.append(name)
                
                # Extract published date
                published = entry.find('{http://www.w3.org/2005/Atom}published').text
                published_date = datetime.fromisoformat(published.replace('Z', '+00:00')).date()
                
                return {
                    'title': title,
                    'authors': ', '.join(authors),
                    'abstract': summary,
                    'published_date': published_date,
                    'journal': 'arXiv'
                }
    except Exception as e:
        print(f"Error fetching arXiv {arxiv_id}: {e}")
    return None

@paper_bp.route('/papers', methods=['POST'])
def add_paper():
    data = request.get_json()
    
    if not data or not data.get('user_id'):
        return jsonify({'error': 'User ID is required'}), 400
    
    doi = data.get('doi')
    arxiv_id = data.get('arxiv_id')
    
    if not doi and not arxiv_id:
        return jsonify({'error': 'Either DOI or arXiv ID is required'}), 400
    
    # Check if paper already exists
    existing_paper = None
    if doi:
        existing_paper = Paper.query.filter_by(doi=doi).first()
    elif arxiv_id:
        existing_paper = Paper.query.filter_by(arxiv_id=arxiv_id).first()
    
    if existing_paper:
        return jsonify({'message': 'Paper already exists', 'paper': existing_paper.to_dict()}), 200
    
    # Fetch paper information
    paper_info = None
    if doi:
        paper_info = fetch_paper_from_doi(doi)
    elif arxiv_id:
        paper_info = fetch_paper_from_arxiv(arxiv_id)
    
    if not paper_info:
        return jsonify({'error': 'Could not fetch paper information'}), 400
    
    # Create new paper
    paper = Paper(
        doi=doi,
        arxiv_id=arxiv_id,
        title=paper_info['title'],
        authors=paper_info['authors'],
        abstract=paper_info['abstract'],
        published_date=paper_info['published_date'],
        journal=paper_info['journal'],
        ai_summary="AI要約：現在開発中です。",  # Placeholder for AI summary
        added_by=data['user_id']
    )
    
    db.session.add(paper)
    db.session.commit()
    
    return jsonify({'message': 'Paper added successfully', 'paper': paper.to_dict()}), 201

@paper_bp.route('/papers', methods=['GET'])
def get_papers():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search = request.args.get('search', '')
    
    query = Paper.query
    
    if search:
        query = query.filter(
            db.or_(
                Paper.title.contains(search),
                Paper.authors.contains(search),
                Paper.abstract.contains(search)
            )
        )
    
    papers = query.order_by(Paper.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'papers': [paper.to_dict() for paper in papers.items],
        'total': papers.total,
        'pages': papers.pages,
        'current_page': page
    })

@paper_bp.route('/papers/<int:paper_id>', methods=['GET'])
def get_paper(paper_id):
    paper = Paper.query.get_or_404(paper_id)
    return jsonify(paper.to_dict())

@paper_bp.route('/papers/<int:paper_id>/comments', methods=['GET'])
def get_comments(paper_id):
    comments = Comment.query.filter_by(paper_id=paper_id, parent_id=None).order_by(
        (Comment.upvotes - Comment.downvotes).desc()
    ).all()
    
    def get_comment_with_replies(comment):
        comment_dict = comment.to_dict()
        replies = Comment.query.filter_by(parent_id=comment.id).order_by(Comment.created_at.asc()).all()
        comment_dict['replies'] = [get_comment_with_replies(reply) for reply in replies]
        return comment_dict
    
    return jsonify([get_comment_with_replies(comment) for comment in comments])

@paper_bp.route('/papers/<int:paper_id>/comments', methods=['POST'])
def add_comment(paper_id):
    data = request.get_json()
    
    if not data or not data.get('user_id') or not data.get('content'):
        return jsonify({'error': 'User ID and content are required'}), 400
    
    comment = Comment(
        paper_id=paper_id,
        user_id=data['user_id'],
        parent_id=data.get('parent_id'),
        content=data['content']
    )
    
    db.session.add(comment)
    db.session.commit()
    
    return jsonify({'message': 'Comment added successfully', 'comment': comment.to_dict()}), 201

@paper_bp.route('/comments/<int:comment_id>/vote', methods=['POST'])
def vote_comment(comment_id):
    data = request.get_json()
    
    if not data or not data.get('user_id') or not data.get('vote_type'):
        return jsonify({'error': 'User ID and vote type are required'}), 400
    
    if data['vote_type'] not in ['upvote', 'downvote']:
        return jsonify({'error': 'Vote type must be upvote or downvote'}), 400
    
    # Check if user already voted
    existing_vote = Vote.query.filter_by(user_id=data['user_id'], comment_id=comment_id).first()
    
    comment = Comment.query.get_or_404(comment_id)
    
    if existing_vote:
        # Update existing vote
        if existing_vote.vote_type != data['vote_type']:
            # Remove old vote count
            if existing_vote.vote_type == 'upvote':
                comment.upvotes -= 1
            else:
                comment.downvotes -= 1
            
            # Add new vote count
            if data['vote_type'] == 'upvote':
                comment.upvotes += 1
            else:
                comment.downvotes += 1
            
            existing_vote.vote_type = data['vote_type']
        # If same vote type, do nothing (could implement toggle here)
    else:
        # Create new vote
        vote = Vote(
            user_id=data['user_id'],
            comment_id=comment_id,
            vote_type=data['vote_type']
        )
        
        if data['vote_type'] == 'upvote':
            comment.upvotes += 1
        else:
            comment.downvotes += 1
        
        db.session.add(vote)
    
    db.session.commit()
    
    return jsonify({'message': 'Vote recorded successfully', 'comment': comment.to_dict()})

@paper_bp.route('/users/<int:user_id>/bookmarks', methods=['GET'])
def get_bookmarks(user_id):
    bookmarks = Bookmark.query.filter_by(user_id=user_id).order_by(Bookmark.created_at.desc()).all()
    return jsonify([bookmark.to_dict() for bookmark in bookmarks])

@paper_bp.route('/users/<int:user_id>/bookmarks', methods=['POST'])
def add_bookmark(user_id):
    data = request.get_json()
    
    if not data or not data.get('paper_id'):
        return jsonify({'error': 'Paper ID is required'}), 400
    
    # Check if bookmark already exists
    existing_bookmark = Bookmark.query.filter_by(user_id=user_id, paper_id=data['paper_id']).first()
    
    if existing_bookmark:
        return jsonify({'message': 'Paper already bookmarked'}), 200
    
    bookmark = Bookmark(
        user_id=user_id,
        paper_id=data['paper_id']
    )
    
    db.session.add(bookmark)
    db.session.commit()
    
    return jsonify({'message': 'Bookmark added successfully', 'bookmark': bookmark.to_dict()}), 201

@paper_bp.route('/users/<int:user_id>/bookmarks/<int:paper_id>', methods=['DELETE'])
def remove_bookmark(user_id, paper_id):
    bookmark = Bookmark.query.filter_by(user_id=user_id, paper_id=paper_id).first_or_404()
    
    db.session.delete(bookmark)
    db.session.commit()
    
    return jsonify({'message': 'Bookmark removed successfully'})

