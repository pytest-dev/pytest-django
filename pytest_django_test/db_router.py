class DbRouter:
    def db_for_read(self, model, **hints):  # noqa: ARG002
        if model._meta.app_label == "app" and model._meta.model_name == "seconditem":
            return "second"
        return None

    def db_for_write(self, model, **hints):  # noqa: ARG002
        if model._meta.app_label == "app" and model._meta.model_name == "seconditem":
            return "second"
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):  # noqa: ARG002
        if app_label == "app" and model_name == "seconditem":
            return db == "second"
