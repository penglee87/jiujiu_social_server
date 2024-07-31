import logging
from flask import Blueprint

from . import posts, users

def create_v3():
    bp = Blueprint('v3', __name__)

    logging.info("Creating v3 blueprint")

    posts.api_rp.register(bp, url_prefix='/posts')
    users.api_rp.register(bp, url_prefix='/users')

    #for rule in bp.url_map.iter_rules():
    #    logging.info(f'Rule: {rule}')

    return bp



    