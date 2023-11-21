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

from sqlalchemy import text
@router.get('/', response_model=schemas.ListPostResponse)
async def get_posts(db: Session = Depends(get_db), limit: int = 1, page: int = 1, search: str = '', user_id: str = Depends(require_user)):
    skip = (page - 1) * limit

    posts = db.query(models.Post).group_by(models.Post.id).filter(
        models.Post.title.contains(search)).limit(limit).offset(skip).all()
    return {'status': 'success', 'results': len(posts), 'posts': posts}


@router.get('/query-string')
# async def get_posts(
#     db: Session = Depends(get_db),
#     limit: int = 100000,
#     page: int = 1,
#     search: str = '',
#     user_id: str = Depends(require_user)
# ):
# async def get_posts(
#     db: Session = Depends(get_db),
# ):
#     try:
#         raw_sql_query = """
#             SELECT post.title, post.content, post.category, post.image, post.user_id, post.id,
#             us.id,
#             us.name,
#             us.email,
#             post.created_at,
#             post.updated_at
#             FROM public.posts as post
#             JOIN public.users as us ON post.user_id = us.id
#             LIMIT 1
#         """
        
#         results = db.execute(raw_sql_query)

#         columns = results.keys()
#         data = [dict(zip(columns, row)) for row in results]
#         return {'status': 'success', 'results': len(data), 'posts': jsonable_encoder(data)}
#     except Exception as e:
#         return JSONResponse(content={"error": str(e)}, status_code=500)



# async def get_posts(db: Session = Depends(get_db)):
#     try:
#         raw_sql_query = """
#             SELECT post.title, post.content, post.category, post.image, post.user_id, post.id,
#             us.id as user_id,
#             us.name,
#             us.email,
#             post.created_at,
#             post.updated_at
#             FROM public.posts as post
#             JOIN public.users as us ON post.user_id = us.id
#             LIMIT 1
#         """

#         result = db.execute(text(raw_sql_query))

#         # Fetch all rows at once
#         rows = result.fetchall()

#         # Assuming you have SQLAlchemy models defined for Post and User
#         columns = result.keys()
#         data = [dict(zip(columns, row)) for row in rows]

#         return {'status': 'success', 'results': len(data), 'posts': jsonable_encoder(data)}
#     except Exception as e:
#         return JSONResponse(content={"error": str(e)}, status_code=500)

async def get_posts(db: Session = Depends(get_db)):
    try:
        raw_sql_query = """
            SELECT post.title, post.content, post.category, post.image, post.user_id, post.id,
            us.id as user_id,
            us.name,
            us.email,
            post.created_at,
            post.updated_at
            FROM public.posts as post
            JOIN public.users as us ON post.user_id = us.id
            LIMIT 1
        """

        rows = await db.fetch_all(query=raw_sql_query)

        # Assuming you have SQLAlchemy models defined for Post and User
        columns = rows[0].keys() if rows else []
        data = [dict(zip(columns, row.values())) for row in rows]

        return {'status': 'success', 'results': len(data), 'posts': jsonable_encoder(data)}
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@router.post('/', status_code=status.HTTP_201_CREATED, response_model=schemas.PostResponse)
async def create_post(post: schemas.CreatePostSchema, db: Session = Depends(get_db), owner_id: str = Depends(require_user)):
    for n in range(1,1001):
        post.user_id = uuid.UUID(owner_id)
        new_post = models.Post(**post.dict())
        db.add(new_post)
        db.commit()
        db.refresh(new_post)
    return new_post


@router.put('/{id}', response_model=schemas.PostResponse)
async def update_post(id: str, post: schemas.UpdatePostSchema, db: Session = Depends(get_db), user_id: str = Depends(require_user)):
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
async def get_post(id: UUID, db: Session = Depends(get_db), user_id: str = Depends(require_user)):
    post = db.query(models.Post).filter(models.Post.id == id).first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"No post with this id: {id} found")
    return post


@router.delete('/{id}')
async def delete_post(id: str, db: Session = Depends(get_db), user_id: str = Depends(require_user)):
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
