# Note that all functions here assume django is available.  So ensure
# this is the case before you call them.


def is_django_unittest(request_or_item):
    """Returns True if the request_or_item is a Django test case, otherwise False"""
    from django.test import SimpleTestCase

    cls = getattr(request_or_item, "cls", None)

    if cls is None:
        return False

    return issubclass(cls, SimpleTestCase)

def get_all_user_model_fields(UserModel):
    """
    Returns all usermodel fields and takes removal of Model._meta.get_all_field_names() into account
    https://docs.djangoproject.com/en/1.9/ref/models/meta/#migrating-from-the-old-api
    """
    try:
        return UserModel._meta.get_all_field_names()
    except AttributeError:
        return [x.name for x in UserModel._meta.get_fields()]
