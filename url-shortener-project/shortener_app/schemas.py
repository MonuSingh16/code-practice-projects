from pydantic import BaseModel

class URLBase(BaseModel):
    # URL that shortened url forwards to
    target_url : str

class URL(URLBase):
    is_active: str # allows to inactive the shortened URL
    clicks: int # no. of time the URL has been visited

    # to provide configuration to pydantic
    class Config:
        # To work with Object Relational Mapping
        # Convenience of interacting with your db using OO Approach 
        orm_mode = True

class URLInfo(URL):
    url: str
    admin_url: str