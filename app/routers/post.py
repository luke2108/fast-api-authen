import uuid
from .. import schemas, models
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status, APIRouter, Response
from app.oauth2 import require_user
from uuid import UUID
router = APIRouter()
from ..database import get_db
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

@router.get('/', response_model=schemas.ListPostResponse)
def get_posts(db: Session = Depends(get_db), limit: int = 1, page: int = 1, search: str = '', user_id: str = Depends(require_user)):
    skip = (page - 1) * limit

    posts = db.query(models.Post).group_by(models.Post.id).filter(
        models.Post.title.contains(search)).limit(limit).offset(skip).all()
    return {'status': 'success', 'results': len(posts), 'posts': posts}


@router.get('/query-string')
def get_posts(
    db: Session = Depends(get_db),
    limit: int = 100000,
    page: int = 1,
    search: str = '',
    user_id: str = Depends(require_user)
):
    try:
        skip = (page - 1) * limit
        raw_sql_query = """
            SELECT post.title, post.content, post.category, post.image, post.user_id, post.id,
                json_build_object(
                    'id', us.id,
                    'name', us.name,
                    'email', us.email
                ) AS user,
                post.created_at,
                post.updated_at
            FROM public.posts as post
            INNER JOIN public.users as us ON post.user_id = us.id
            LIMIT 1
        """
        
        # Execute the raw SQL query
        results = db.execute(raw_sql_query)

        # Fetch the columns and create a list of dictionaries
        columns = results.keys()
        data = [dict(zip(columns, row)) for row in results]
        return {'status': 'success', 'results': len(data), 'posts': jsonable_encoder(data)}
        # return JSONResponse(content=jsonable_encoder(data), status_code=200)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@router.post('/', status_code=status.HTTP_201_CREATED, response_model=schemas.PostResponse)
def create_post(post: schemas.CreatePostSchema, db: Session = Depends(get_db), owner_id: str = Depends(require_user)):
    for n in range(1,1001):
        post.user_id = uuid.UUID(owner_id)
        new_post = models.Post(**post.dict())
        db.add(new_post)
        db.commit()
        db.refresh(new_post)
    return new_post


@router.put('/{id}', response_model=schemas.PostResponse)
def update_post(id: str, post: schemas.UpdatePostSchema, db: Session = Depends(get_db), user_id: str = Depends(require_user)):
    post_query = db.query(models.Post).filter(models.Post.id == id)
    updated_post = post_query.first()

    if not updated_post:
        raise HTTPException(status_code=status.HTTP_200_OK,
                            detail=f'No post with this id: {id} found')
    if updated_post.user_id != uuid.UUID(user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail='You are not allowed to perform this action')
    post.user_id = user_id
    post_query.update(post.dict(exclude_unset=True), synchronize_session=False)
    db.commit()
    return updated_post


@router.get('/{id}', response_model=schemas.PostResponse)
def get_post(id: UUID, db: Session = Depends(get_db), user_id: str = Depends(require_user)):
    post = db.query(models.Post).filter(models.Post.id == id).first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"No post with this id: {id} found")
    return post


@router.delete('/{id}')
def delete_post(id: str, db: Session = Depends(get_db), user_id: str = Depends(require_user)):
    post_query = db.query(models.Post).filter(models.Post.id == id)
    post = post_query.first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'No post with this id: {id} found')

    if str(post.user_id) != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail='You are not allowed to perform this action')
    post_query.delete(synchronize_session=False)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
