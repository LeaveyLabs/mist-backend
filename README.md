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
* query_parameters: text, location, date
* authorization: none

### GET api/commments/
* query_parameters: post_id
* authorization: none

### GET api/messages/
* query_parameters: none
* authorization: token

### GET api/votes/
* query_parameters: username, post_id
* authorization: none

### POST api/profiles/
* query_parameters: username, first_name, last_name
* authorization: token

### POST api/posts/
* query_parameters: title, text, date, author
* authorization: none

### POST api/comments/
* query_parameters: text, date, post, author
* authorization: none

### POST api/messages/
* query_parameters: text, date, from_user, to_user
* authorization: token

### POST api/flags/
* query_parameters: voter, post, timestamp, rating
* authorization: none

### POST api/flags/
* query_parameters: flagger, post, timestamp, rating
* authorization: none
