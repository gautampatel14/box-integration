ADDON_NAME = "box_integration_for_splunk"
ACCOUNT_CONF = "box_integration_for_splunk_account.conf"
REST_URL = "https://api.box.com/2.0"
URL = "https://api.box.com"
TIMEOUT = 60
RETRYS = 5
USER_FIELDS = "id,type,name,login,created_at,modified_at,language,timezone,space_amount,space_used,max_upload_size,status,job_title,phone,address,avatar_url,notification_email,role,tracking_codes,can_see_managed_users,is_sync_enabled,is_external_collab_restricted,is_exempt_from_device_limits,is_exempt_from_login_verification,enterprise,my_tags,hostname,is_platform_access_only,external_app_user_id"
FOLDERS_FIELDS = "type,id,name,size,sequence_id,etag,item_status,permissions,created_at,modified_at,has_collaborations,can_non_owners_invite,tags,created_by,modified_by,parent,path_collection,shared_link"
COLLABORATION_FIELDS = " type,id,created_by,created_at,modified_at,expires_at,status,accessible_by,role,acknowledged_at,item"
FILE_FIELDS = "type,id,name,owned_by,comment_count,version_number,created_at,modified_at,purged_at,trashed_at,size,content_created_at,content_modified_at,file_version,description,path_collection,shared_link"
COMMENT_FIELDS = "type,id,is_reply_comment,message,tagged_message,item,modified_at,created_by,created_at"
TASK_FIELDS = "type,id,item,due_at,action,message,is_completed,created_by,created_at"
