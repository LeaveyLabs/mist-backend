import math

# Comment Content Moderation
def is_impermissible_comment(votecount, flagcount):
    LOWER_FLAG_BOUND = 2
    return flagcount > LOWER_FLAG_BOUND and flagcount > math.sqrt(votecount)

def is_beyond_impermissible_comment_limit(serialized_comments):
    IMPERMISSIBLE_COMMENT_LIMIT = 10
    impermissible_comments = 0
    for serialized_comment in serialized_comments:
        votecount = serialized_comment.get('votecount')
        flagcount = serialized_comment.get('flagcount')
        if is_impermissible_comment(votecount, flagcount):
            impermissible_comments += 1
    return impermissible_comments > IMPERMISSIBLE_COMMENT_LIMIT

# Post Content Moderation
def is_impermissible_post(votecount, flagcount):
    LOWER_FLAG_BOUND = 2
    return flagcount > LOWER_FLAG_BOUND and flagcount > math.sqrt(votecount)

def is_beyond_impermissible_post_limit(serialized_posts):
    IMPERMISSIBLE_POST_LIMIT = 10
    impermissible_posts = 0
    for serialized_post in serialized_posts:
        votecount = serialized_post.get('votecount')
        flagcount = serialized_post.get('flagcount')
        if is_impermissible_post(votecount, flagcount):
            impermissible_posts += 1
    return impermissible_posts > IMPERMISSIBLE_POST_LIMIT