#!/usr/bin/env python3

# Author::    Justin Flannery  (mailto:juftin@juftin.com)

"""
Endpoints for Creating / Deleting Images
"""
from json import loads
import logging
from os import getenv
from urllib.parse import urljoin

from dotenv import load_dotenv
from flask import abort, Blueprint, jsonify, request, Response
from flask_login import login_required
from requests.api import delete, post

from adjuftments.config import APIEndpoints, DOT_ENV_FILE_PATH

load_dotenv(DOT_ENV_FILE_PATH, override=True)
logger = logging.getLogger(__name__)

images = Blueprint(name="images", import_name=__name__)


@images.route(rule=APIEndpoints.IMAGES_ENDPOINT, methods=["POST"])
@login_required
def upload_imgur_image() -> Response:
    """
    Upload an Image to Imgur

    Returns
    -------
    Response
    """
    imgur_api_url = "https://api.imgur.com/3/image"
    headers = dict(Authorization=f"Client-ID {getenv('IMGUR_CLIENT_ID')}")
    response = post(url=imgur_api_url,
                    headers=headers,
                    data=request.get_data(),
                    files=list())
    if response.status_code != 200:
        logger.error(response.text)
        abort(status=response.status_code, description=response.text)
    return jsonify(loads(response.content))


@images.route(rule=f"{APIEndpoints.IMAGES_ENDPOINT}/<image_delete_hash>", methods=["DELETE"])
@login_required
def delete_imgur_image(image_delete_hash: str) -> Response:
    """
    Delete an image from Imgur

    Parameters
    ----------
    image_delete_hash : str
        Imgur Delete Hash

    Returns
    -------
    Response
    """
    imgur_api_url = urljoin("https://api.imgur.com/3/image", image_delete_hash)
    headers = dict(Authorization=f"Client-ID {getenv('IMGUR_CLIENT_ID')}")
    response = delete(imgur_api_url, headers=headers,
                      data=dict(), files=dict())
    if response.status_code != 200:
        abort(status=response.status_code, description=response.text)
    return jsonify(loads(response.content))
