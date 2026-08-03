from collections.abc import Callable, Iterable, Iterator, Sequence
from contextlib import AbstractContextManager
from typing import Any, overload

from django import forms
from django.contrib.messages import Message
from django.db.models import Model, QuerySet, RawQuerySet
from django.http.response import HttpResponseBase

def assertRedirects(
    response: HttpResponseBase,
    expected_url: str,
    status_code: int = ...,
    target_status_code: int = ...,
    msg_prefix: str = ...,
    fetch_redirect_response: bool = ...,
) -> None: ...
def assertURLEqual(
    url1: str,
    url2: str,
    msg_prefix: str = ...,
) -> None: ...
def assertContains(
    response: HttpResponseBase,
    text: object,
    count: int | None = ...,
    status_code: int = ...,
    msg_prefix: str = ...,
    html: bool = False,
) -> None: ...
def assertNotContains(
    response: HttpResponseBase,
    text: object,
    status_code: int = ...,
    msg_prefix: str = ...,
    html: bool = False,
) -> None: ...
def assertFormError(
    form: forms.BaseForm,
    field: str | None,
    errors: str | Sequence[str],
    msg_prefix: str = ...,
) -> None: ...
def assertFormSetError(
    formset: forms.BaseFormSet,
    form_index: int | None,
    field: str | None,
    errors: str | Sequence[str],
    msg_prefix: str = ...,
) -> None: ...

# with assertTemplateUsed("template.html"): ...  # noqa: ERA001
@overload
def assertTemplateUsed(
    response: str,
    template_name: None = ...,
    msg_prefix: str = ...,
    count: int | None = ...,
) -> AbstractContextManager[Any]: ...

# with assertTemplateUsed(template_name="template.html"): ...  # noqa: ERA001
@overload
def assertTemplateUsed(
    response: None = ...,
    template_name: str | None = ...,
    msg_prefix: str = ...,
    count: int | None = ...,
) -> AbstractContextManager[Any]: ...

# assertTemplateUsed(response, "template.html")  # noqa: ERA001
@overload
def assertTemplateUsed(
    response: HttpResponseBase,
    template_name: str | None = ...,
    msg_prefix: str = ...,
    count: int | None = ...,
) -> None: ...

# with assertTemplateNotUsed("template.html"): ...  # noqa: ERA001
@overload
def assertTemplateNotUsed(
    response: str,
    template_name: None = ...,
    msg_prefix: str = ...,
) -> AbstractContextManager[Any]: ...

# with assertTemplateNotUsed(template_name="template.html"): ...  # noqa: ERA001
@overload
def assertTemplateNotUsed(
    response: None = ...,
    template_name: str | None = ...,
    msg_prefix: str = ...,
) -> AbstractContextManager[Any]: ...

# assertTemplateNotUsed(response, "template.html")  # noqa: ERA001
@overload
def assertTemplateNotUsed(
    response: HttpResponseBase,
    template_name: str | None = ...,
    msg_prefix: str = ...,
) -> None: ...
def assertRaisesMessage(
    expected_exception: type[Exception],
    expected_message: str,
    *args: Any,
    **kwargs: Any,
) -> Any: ...
def assertWarnsMessage(
    expected_warning: Warning,
    expected_message: str,
    *args: Any,
    **kwargs: Any,
) -> Any: ...
def assertFieldOutput(
    fieldclass: type[forms.Field],
    valid: Any,
    invalid: Any,
    field_args: Any = ...,
    field_kwargs: Any = ...,
    empty_value: str = ...,
) -> Any: ...
def assertHTMLEqual(
    html1: str,
    html2: str,
    msg: str | None = ...,
) -> None: ...
def assertHTMLNotEqual(
    html1: str,
    html2: str,
    msg: str | None = ...,
) -> None: ...
def assertInHTML(
    needle: str,
    haystack: str,
    count: int | None = ...,
    msg_prefix: str = ...,
) -> None: ...

# Added in Django 5.1.
def assertNotInHTML(
    needle: str,
    haystack: str,
    msg_prefix: str = ...,
) -> None: ...
def assertJSONEqual(
    raw: str,
    expected_data: Any,
    msg: str | None = ...,
) -> None: ...
def assertJSONNotEqual(
    raw: str,
    expected_data: Any,
    msg: str | None = ...,
) -> None: ...
def assertXMLEqual(
    xml1: str,
    xml2: str,
    msg: str | None = ...,
) -> None: ...
def assertXMLNotEqual(
    xml1: str,
    xml2: str,
    msg: str | None = ...,
) -> None: ...

# Removed in Django 5.1: use assertQuerySetEqual.
def assertQuerysetEqual(
    qs: Iterator[Any] | list[Model] | QuerySet | RawQuerySet,
    values: Iterable[Any],
    transform: Callable[[Model], Any] | type[str] | None = ...,
    ordered: bool = ...,
    msg: str | None = ...,
) -> None: ...
def assertQuerySetEqual(
    qs: Iterator[Any] | list[Model] | QuerySet | RawQuerySet,
    values: Iterable[Any],
    transform: Callable[[Model], Any] | type[str] | None = ...,
    ordered: bool = ...,
    msg: str | None = ...,
) -> None: ...
@overload
def assertNumQueries(
    num: int, func: None = None, *, using: str = ...
) -> AbstractContextManager[Any]: ...
@overload
def assertNumQueries(
    num: int, func: Callable[..., Any], *args: Any, using: str = ..., **kwargs: Any
) -> None: ...

# Added in Django 5.0.
def assertMessages(
    response: HttpResponseBase,
    expected_messages: Sequence[Message],
    *args: Any,
    ordered: bool = ...,
) -> None: ...

# Fallback in case Django adds new asserts.
def __getattr__(name: str) -> Callable[..., Any]: ...
