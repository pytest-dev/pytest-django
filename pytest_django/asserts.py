"""
Dynamically load all Django assertion cases and expose them for importing.
"""
from functools import wraps
from typing import Any, Callable, Optional, Sequence, Set, Union

from django.test import (
    LiveServerTestCase, SimpleTestCase, TestCase, TransactionTestCase,
)


TYPE_CHECKING = False


test_case = TestCase("run")


def _wrapper(name: str):
    func = getattr(test_case, name)

    @wraps(func)
    def assertion_func(*args, **kwargs):
        return func(*args, **kwargs)

    return assertion_func


__all__ = []
assertions_names = set()  # type: Set[str]
assertions_names.update(
    {attr for attr in vars(TestCase) if attr.startswith("assert")},
    {attr for attr in vars(SimpleTestCase) if attr.startswith("assert")},
    {attr for attr in vars(LiveServerTestCase) if attr.startswith("assert")},
    {attr for attr in vars(TransactionTestCase) if attr.startswith("assert")},
)

for assert_func in assertions_names:
    globals()[assert_func] = _wrapper(assert_func)
    __all__.append(assert_func)


if TYPE_CHECKING:
    from django.http import HttpResponse

    def assertRedirects(
        response: HttpResponse,
        expected_url: str,
        status_code: int = ...,
        target_status_code: int = ...,
        msg_prefix: str = ...,
        fetch_redirect_response: bool = ...,
    ) -> None:
        ...

    def assertURLEqual(
        url1: str,
        url2: str,
        msg_prefix: str = ...,
    ) -> None:
        ...

    def assertContains(
        response: HttpResponse,
        text: object,
        count: Optional[int] = ...,
        status_code: int = ...,
        msg_prefix: str = ...,
        html: bool = False,
    ) -> None:
        ...

    def assertNotContains(
        response: HttpResponse,
        text: object,
        status_code: int = ...,
        msg_prefix: str = ...,
        html: bool = False,
    ) -> None:
        ...

    def assertFormError(
        response: HttpResponse,
        form: str,
        field: Optional[str],
        errors: Union[str, Sequence[str]],
        msg_prefix: str = ...,
    ) -> None:
        ...

    def assertFormsetError(
        response: HttpResponse,
        formset: str,
        form_index: Optional[int],
        field: Optional[str],
        errors: Union[str, Sequence[str]],
        msg_prefix: str = ...,
    ) -> None:
        ...

    def assertTemplateUsed(
        response: Optional[HttpResponse] = ...,
        template_name: Optional[str] = ...,
        msg_prefix: str = ...,
        count: Optional[int] = ...,
    ):
        ...

    def assertTemplateNotUsed(
        response: Optional[HttpResponse] = ...,
        template_name: Optional[str] = ...,
        msg_prefix: str = ...,
    ):
        ...

    def assertRaisesMessage(
        expected_exception: BaseException,
        expected_message: str,
        *args,
        **kwargs
    ):
        ...

    def assertWarnsMessage(
        expected_warning: Warning,
        expected_message: str,
        *args,
        **kwargs
    ):
        ...

    def assertFieldOutput(
        fieldclass,
        valid,
        invalid,
        field_args=...,
        field_kwargs=...,
        empty_value: str = ...,
    ) -> None:
        ...

    def assertHTMLEqual(
        html1: str,
        html2: str,
        msg: Optional[str] = ...,
    ) -> None:
        ...

    def assertHTMLNotEqual(
        html1: str,
        html2: str,
        msg: Optional[str] = ...,
    ) -> None:
        ...

    def assertInHTML(
        needle: str,
        haystack: str,
        count: Optional[int] = ...,
        msg_prefix: str = ...,
    ) -> None:
        ...

    def assertJSONEqual(
        raw: str,
        expected_data: Any,
        msg: Optional[str] = ...,
    ) -> None:
        ...

    def assertJSONNotEqual(
        raw: str,
        expected_data: Any,
        msg: Optional[str] = ...,
    ) -> None:
        ...

    def assertXMLEqual(
        xml1: str,
        xml2: str,
        msg: Optional[str] = ...,
    ) -> None:
        ...

    def assertXMLNotEqual(
        xml1: str,
        xml2: str,
        msg: Optional[str] = ...,
    ) -> None:
        ...

    def assertQuerysetEqual(
        qs,
        values,
        transform=...,
        ordered: bool = ...,
        msg: Optional[str] = ...,
    ) -> None:
        ...

    def assertNumQueries(
        num: int,
        func=...,
        *args,
        using: str = ...,
        **kwargs
    ):
        ...

    # Fallback in case Django adds new asserts.
    def __getattr__(name: str) -> Callable[..., Any]:
        ...
