# Authorization

### POST api-register/
* query_parameters: email, username, password

### POST api-token-auth/
* query_parameters: username, password

# Entities

### GET api/profiles/
* query_parameters: username
* authorization: token

### GET api/posts/
* query_parameters: none
* authorization: token

### GET api/commments/
* query_parameters: post_id
* authorization: token

### GET api/messages/
* query_parameters: none
* authorization: token

### POST api/profiles/
* query_parameters: username, first_name, last_name
* authorization: token

### POST api/posts/
* query_parameters: title, text, date, author
* authorization: token

### POST api/comments/
* query_parameters: text, date, post, author
* authorization: token

### POST api/messages/
* query_parameters: text, date, from_user, to_user
* authorization: token
