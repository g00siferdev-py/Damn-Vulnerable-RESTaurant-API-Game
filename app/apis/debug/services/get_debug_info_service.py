import os
import platform
import sys

import psutil
from apis.auth.utils import RolesBasedAuthChecker, get_current_user
from db.models import User, UserRole
from fastapi import APIRouter, Depends, status
from typing_extensions import Annotated

router = APIRouter()


@router.get("/debug", status_code=status.HTTP_200_OK)
def get_debug_info_service(
    current_user: Annotated[User, Depends(get_current_user)],
    auth=Depends(RolesBasedAuthChecker([UserRole.CHEF])),
):
    os_info = {
        "system": platform.system(),
        "node": platform.node(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
    }

    env_vars = dict(os.environ)
    # Mask sensitive environment values so a debug dump cannot leak secrets.
    sensitive_keys = {"password", "secret", "token", "key", "postgres"}
    for key in list(env_vars.keys()):
        if any(s in key.lower() for s in sensitive_keys):
            env_vars[key] = "***REDACTED***"

    local_paths = {
        "current_working_directory": os.getcwd(),
        "sys_path": sys.path,
    }

    disk_usage = psutil.disk_usage(os.getcwd())
    disk_info = {
        "total": disk_usage.total,
        "used": disk_usage.used,
        "free": disk_usage.free,
        "percent": disk_usage.percent,
    }

    mem = psutil.virtual_memory()
    memory_info = {
        "total": mem.total,
        "available": mem.available,
        "used": mem.used,
        "free": mem.free,
        "percent": mem.percent,
    }

    debug_info = {
        "os_info": os_info,
        "env_vars": env_vars,
        "local_paths": local_paths,
        "disk_usage": disk_info,
        "memory_usage": memory_info,
    }

    return debug_info
