"""
Dynamically load all Django assertion cases and expose them for importing.
"""

from __future__ import annotations

from functools import wraps
from typing import TYPE_CHECKING

from django import VERSION
from django.test import LiveServerTestCase, SimpleTestCase, TestCase, TransactionTestCase


USE_CONTRIB_MESSAGES = VERSION >= (5, 0)

if USE_CONTRIB_MESSAGES:
    from django.contrib.messages import Message
    from django.contrib.messages.test import MessagesTestMixin

    class MessagesTestCase(MessagesTestMixin, TestCase):
        pass

    test_case = MessagesTestCase("run")
else:
    test_case = TestCase("run")

if TYPE_CHECKING:
    from collections.abc import Callable, Collection, Iterator, Sequence
    from contextlib import AbstractContextManager
    from typing import Any, overload

    from django import forms
    from django.db.models import Model, QuerySet, RawQuerySet
    from django.http.response import HttpResponseBase


def _wrapper(name: str) -> Callable[..., Any]:
    func = getattr(test_case, name)

    @wraps(func)
    def assertion_func(*args: Any, **kwargs: Any) -> Any:
        return func(*args, **kwargs)

    return assertion_func


__all__ = []
assertions_names: set[str] = set()
assertions_names.update(
    {attr for attr in vars(TestCase) if attr.startswith("assert")},
    {attr for attr in vars(SimpleTestCase) if attr.startswith("assert")},
    {attr for attr in vars(LiveServerTestCase) if attr.startswith("assert")},
    {attr for attr in vars(TransactionTestCase) if attr.startswith("assert")},
)

if USE_CONTRIB_MESSAGES:
    assertions_names.update(
        {attr for attr in vars(MessagesTestMixin) if attr.startswith("assert")},
    )

for assert_func in assertions_names:
    globals()[assert_func] = _wrapper(assert_func)
    __all__.append(assert_func)  # noqa: PYI056


if TYPE_CHECKING:

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

    def assertTemplateUsed(
        response: HttpResponseBase | str | None = ...,
        template_name: str | None = ...,
        msg_prefix: str = ...,
        count: int | None = ...,
    ) -> None: ...

    def assertTemplateNotUsed(
        response: HttpResponseBase | str | None = ...,
        template_name: str | None = ...,
        msg_prefix: str = ...,
    ) -> None: ...

    def assertRaisesMessage(
        expected_exception: type[Exception],
        expected_message: str,
        *args: Any,
        **kwargs: Any,
    ) -> None: ...

    def assertWarnsMessage(
        expected_warning: Warning,
        expected_message: str,
        *args: Any,
        **kwargs: Any,
    ) -> None: ...

    def assertFieldOutput(
        fieldclass: type[forms.Field],
        valid: Any,
        invalid: Any,
        field_args: Any = ...,
        field_kwargs: Any = ...,
        empty_value: str = ...,
    ) -> None: ...

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
        values: Collection[Any],
        transform: Callable[[Model], Any] | type[str] | None = ...,
        ordered: bool = ...,
        msg: str | None = ...,
    ) -> None: ...

    def assertQuerySetEqual(
        qs: Iterator[Any] | list[Model] | QuerySet | RawQuerySet,
        values: Collection[Any],
        transform: Callable[[Model], Any] | type[str] | None = ...,
        ordered: bool = ...,
        msg: str | None = ...,
    ) -> None: ...

    @overload
    def assertNumQueries(
        num: int, func: None = None, *, using: str = ...
    ) -> AbstractContextManager[None]: ...

    @overload
    def assertNumQueries(
        num: int, func: Callable[..., Any], *args: Any, using: str = ..., **kwargs: Any
    ) -> None: ...

    def assertNumQueries(
        num: int,
        func=...,
        *args: Any,
        using: str = ...,
        **kwargs: Any,
    ): ...

    # Added in Django 5.0.
    def assertMessages(
        response: HttpResponseBase,
        expected_messages: Sequence[Message],
        *args: Any,
        ordered: bool = ...,
    ) -> None: ...

    # Fallback in case Django adds new asserts.
    def __getattr__(name: str) -> Callable[..., Any]: ...
