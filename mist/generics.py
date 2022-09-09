import math

# Comment Content Moderation
LOWER_COMMENT_FLAG_BOUND = 2
IMPERMISSIBLE_COMMENT_LIMIT = 10

def is_impermissible_comment(serialized_comment):
    votecount = serialized_comment.get('votecount')
    flagcount = serialized_comment.get('flagcount')
    return flagcount > LOWER_COMMENT_FLAG_BOUND and flagcount*flagcount > votecount

def is_beyond_impermissible_comment_limit(serialized_comments):
    impermissible_comments = 0
    for serialized_comment in serialized_comments:
        if is_impermissible_comment(serialized_comment):
            impermissible_comments += 1
    return impermissible_comments > IMPERMISSIBLE_COMMENT_LIMIT

# Post Content Moderation
LOWER_POST_FLAG_BOUND = 2
IMPERMISSIBLE_POST_LIMIT = 10

def is_impermissible_post(serialized_post):
    votecount = serialized_post.get('votecount')
    flagcount = serialized_post.get('flagcount')
    return flagcount > LOWER_POST_FLAG_BOUND and flagcount*flagcount > votecount

def is_beyond_impermissible_post_limit(serialized_posts):
    impermissible_posts = 0
    for serialized_post in serialized_posts:
        if is_impermissible_post(serialized_post):
            impermissible_posts += 1
    return impermissible_posts > IMPERMISSIBLE_POST_LIMIT