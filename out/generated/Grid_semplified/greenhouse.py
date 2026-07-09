from __future__ import annotations

# Generated algebraic input module from CIF automaton/template: Greenhouse_template

import math
import re
from typing import Iterable, Any


TEMPLATE_NAME = 'Greenhouse_template'
MODULE_NAME = 'Greenhouse'
INPUT_NAMES = ['T_in', 'Rad', 'T_mean', 'T_daytime_mean']
ALGEBRAIC_LIST_SPECS = {'Rad_input': ['Rad*1.0', 'Rad*0.9987654320987654', 'Rad*0.9975308641975309', 'Rad*0.9962962962962963', 'Rad*0.9950617283950617', 'Rad*0.9938271604938271', 'Rad*0.9925925925925926', 'Rad*0.991358024691358', 'Rad*0.9901234567901235', 'Rad*0.9888888888888889', 'Rad*0.9876543209876543', 'Rad*0.9864197530864197', 'Rad*0.9851851851851852', 'Rad*0.9839506172839506', 'Rad*0.9827160493827161', 'Rad*0.9814814814814815', 'Rad*0.980246913580247', 'Rad*0.9790123456790123', 'Rad*0.9777777777777777', 'Rad*0.9765432098765432', 'Rad*0.9753086419753086', 'Rad*0.9740740740740741', 'Rad*0.9728395061728395', 'Rad*0.971604938271605', 'Rad*0.9703703703703703', 'Rad*0.9691358024691358', 'Rad*0.9679012345679012', 'Rad*0.9666666666666667', 'Rad*0.9654320987654321', 'Rad*0.9641975308641976', 'Rad*0.962962962962963', 'Rad*0.9617283950617284', 'Rad*0.9604938271604938', 'Rad*0.9592592592592593', 'Rad*0.9580246913580247', 'Rad*0.9567901234567902', 'Rad*0.9555555555555556', 'Rad*0.9543209876543209', 'Rad*0.9530864197530864', 'Rad*0.9518518518518518', 'Rad*0.9506172839506173', 'Rad*0.9493827160493827', 'Rad*0.9481481481481482', 'Rad*0.9469135802469136', 'Rad*0.945679012345679', 'Rad*0.9444444444444444', 'Rad*0.9432098765432099', 'Rad*0.9419753086419753', 'Rad*0.9407407407407408', 'Rad*0.9395061728395062', 'Rad*0.9382716049382716', 'Rad*0.937037037037037', 'Rad*0.9358024691358025', 'Rad*0.9345679012345679', 'Rad*0.9333333333333333', 'Rad*0.9320987654320988', 'Rad*0.9308641975308642', 'Rad*0.9296296296296296', 'Rad*0.928395061728395', 'Rad*0.9271604938271605', 'Rad*0.9259259259259259', 'Rad*0.9246913580246914', 'Rad*0.9234567901234568', 'Rad*0.9222222222222222', 'Rad*0.9209876543209876', 'Rad*0.9197530864197531', 'Rad*0.9185185185185185', 'Rad*0.917283950617284', 'Rad*0.9160493827160494', 'Rad*0.9148148148148149', 'Rad*0.9135802469135803', 'Rad*0.9123456790123456', 'Rad*0.9111111111111111', 'Rad*0.9098765432098765', 'Rad*0.908641975308642', 'Rad*0.9074074074074074', 'Rad*0.9061728395061728', 'Rad*0.9049382716049382', 'Rad*0.9037037037037037', 'Rad*0.9024691358024691', 'Rad*1.0', 'Rad*0.9987654320987654', 'Rad*0.9975308641975309', 'Rad*0.9962962962962963', 'Rad*0.9950617283950617', 'Rad*0.9938271604938271', 'Rad*0.9925925925925926', 'Rad*0.991358024691358', 'Rad*0.9901234567901235', 'Rad*0.9888888888888889', 'Rad*0.9876543209876543', 'Rad*0.9864197530864197', 'Rad*0.9851851851851852', 'Rad*0.9839506172839506', 'Rad*0.9827160493827161', 'Rad*0.9814814814814815', 'Rad*0.980246913580247', 'Rad*0.9790123456790123', 'Rad*0.9777777777777777', 'Rad*0.9765432098765432'], 'T_input': ['T_in + Rad*(1.0)/300', 'T_in + Rad*(0.9987654320987654)/300', 'T_in + Rad*(0.9975308641975309)/300', 'T_in + Rad*(0.9962962962962963)/300', 'T_in + Rad*(0.9950617283950617)/300', 'T_in + Rad*(0.9938271604938271)/300', 'T_in + Rad*(0.9925925925925926)/300', 'T_in + Rad*(0.991358024691358)/300', 'T_in + Rad*(0.9901234567901235)/300', 'T_in + Rad*(0.9888888888888889)/300', 'T_in + Rad*(0.9876543209876543)/300', 'T_in + Rad*(0.9864197530864197)/300', 'T_in + Rad*(0.9851851851851852)/300', 'T_in + Rad*(0.9839506172839506)/300', 'T_in + Rad*(0.9827160493827161)/300', 'T_in + Rad*(0.9814814814814815)/300', 'T_in + Rad*(0.980246913580247)/300', 'T_in + Rad*(0.9790123456790123)/300', 'T_in + Rad*(0.9777777777777777)/300', 'T_in + Rad*(0.9765432098765432)/300', 'T_in + Rad*(0.9753086419753086)/300', 'T_in + Rad*(0.9740740740740741)/300', 'T_in + Rad*(0.9728395061728395)/300', 'T_in + Rad*(0.971604938271605)/300', 'T_in + Rad*(0.9703703703703703)/300', 'T_in + Rad*(0.9691358024691358)/300', 'T_in + Rad*(0.9679012345679012)/300', 'T_in + Rad*(0.9666666666666667)/300', 'T_in + Rad*(0.9654320987654321)/300', 'T_in + Rad*(0.9641975308641976)/300', 'T_in + Rad*(0.962962962962963)/300', 'T_in + Rad*(0.9617283950617284)/300', 'T_in + Rad*(0.9604938271604938)/300', 'T_in + Rad*(0.9592592592592593)/300', 'T_in + Rad*(0.9580246913580247)/300', 'T_in + Rad*(0.9567901234567902)/300', 'T_in + Rad*(0.9555555555555556)/300', 'T_in + Rad*(0.9543209876543209)/300', 'T_in + Rad*(0.9530864197530864)/300', 'T_in + Rad*(0.9518518518518518)/300', 'T_in + Rad*(0.9506172839506173)/300', 'T_in + Rad*(0.9493827160493827)/300', 'T_in + Rad*(0.9481481481481482)/300', 'T_in + Rad*(0.9469135802469136)/300', 'T_in + Rad*(0.945679012345679)/300', 'T_in + Rad*(0.9444444444444444)/300', 'T_in + Rad*(0.9432098765432099)/300', 'T_in + Rad*(0.9419753086419753)/300', 'T_in + Rad*(0.9407407407407408)/300', 'T_in + Rad*(0.9395061728395062)/300', 'T_in + Rad*(0.9382716049382716)/300', 'T_in + Rad*(0.937037037037037)/300', 'T_in + Rad*(0.9358024691358025)/300', 'T_in + Rad*(0.9345679012345679)/300', 'T_in + Rad*(0.9333333333333333)/300', 'T_in + Rad*(0.9320987654320988)/300', 'T_in + Rad*(0.9308641975308642)/300', 'T_in + Rad*(0.9296296296296296)/300', 'T_in + Rad*(0.928395061728395)/300', 'T_in + Rad*(0.9271604938271605)/300', 'T_in + Rad*(0.9259259259259259)/300', 'T_in + Rad*(0.9246913580246914)/300', 'T_in + Rad*(0.9234567901234568)/300', 'T_in + Rad*(0.9222222222222222)/300', 'T_in + Rad*(0.9209876543209876)/300', 'T_in + Rad*(0.9197530864197531)/300', 'T_in + Rad*(0.9185185185185185)/300', 'T_in + Rad*(0.917283950617284)/300', 'T_in + Rad*(0.9160493827160494)/300', 'T_in + Rad*(0.9148148148148149)/300', 'T_in + Rad*(0.9135802469135803)/300', 'T_in + Rad*(0.9123456790123456)/300', 'T_in + Rad*(0.9111111111111111)/300', 'T_in + Rad*(0.9098765432098765)/300', 'T_in + Rad*(0.908641975308642)/300', 'T_in + Rad*(0.9074074074074074)/300', 'T_in + Rad*(0.9061728395061728)/300', 'T_in + Rad*(0.9049382716049382)/300', 'T_in + Rad*(0.9037037037037037)/300', 'T_in + Rad*(0.9024691358024691)/300', 'T_in + Rad*(1.0071428571428571)/300', 'T_in + Rad*(1.0059082892416227)/300', 'T_in + Rad*(1.004673721340388)/300', 'T_in + Rad*(1.0034391534391536)/300', 'T_in + Rad*(1.002204585537919)/300', 'T_in + Rad*(1.0009700176366843)/300', 'T_in + Rad*(0.9997354497354497)/300', 'T_in + Rad*(0.9985008818342151)/300', 'T_in + Rad*(0.9972663139329806)/300', 'T_in + Rad*(0.996031746031746)/300', 'T_in + Rad*(0.9947971781305114)/300', 'T_in + Rad*(0.9935626102292768)/300', 'T_in + Rad*(0.9923280423280423)/300', 'T_in + Rad*(0.9910934744268077)/300', 'T_in + Rad*(0.9898589065255732)/300', 'T_in + Rad*(0.9886243386243386)/300', 'T_in + Rad*(0.9873897707231041)/300', 'T_in + Rad*(0.9861552028218694)/300', 'T_in + Rad*(0.9849206349206349)/300', 'T_in + Rad*(0.9836860670194003)/300'], 'T_sparse_mean': ['T_mean + Rad*(1.0)/300', 'T_mean + Rad*(0.9987654320987654)/300', 'T_mean + Rad*(0.9975308641975309)/300', 'T_mean + Rad*(0.9962962962962963)/300', 'T_mean + Rad*(0.9950617283950617)/300', 'T_mean + Rad*(0.9938271604938271)/300', 'T_mean + Rad*(0.9925925925925926)/300', 'T_mean + Rad*(0.991358024691358)/300', 'T_mean + Rad*(0.9901234567901235)/300', 'T_mean + Rad*(0.9888888888888889)/300', 'T_mean + Rad*(0.9876543209876543)/300', 'T_mean + Rad*(0.9864197530864197)/300', 'T_mean + Rad*(0.9851851851851852)/300', 'T_mean + Rad*(0.9839506172839506)/300', 'T_mean + Rad*(0.9827160493827161)/300', 'T_mean + Rad*(0.9814814814814815)/300', 'T_mean + Rad*(0.980246913580247)/300', 'T_mean + Rad*(0.9790123456790123)/300', 'T_mean + Rad*(0.9777777777777777)/300', 'T_mean + Rad*(0.9765432098765432)/300', 'T_mean + Rad*(0.9753086419753086)/300', 'T_mean + Rad*(0.9740740740740741)/300', 'T_mean + Rad*(0.9728395061728395)/300', 'T_mean + Rad*(0.971604938271605)/300', 'T_mean + Rad*(0.9703703703703703)/300', 'T_mean + Rad*(0.9691358024691358)/300', 'T_mean + Rad*(0.9679012345679012)/300', 'T_mean + Rad*(0.9666666666666667)/300', 'T_mean + Rad*(0.9654320987654321)/300', 'T_mean + Rad*(0.9641975308641976)/300', 'T_mean + Rad*(0.962962962962963)/300', 'T_mean + Rad*(0.9617283950617284)/300', 'T_mean + Rad*(0.9604938271604938)/300', 'T_mean + Rad*(0.9592592592592593)/300', 'T_mean + Rad*(0.9580246913580247)/300', 'T_mean + Rad*(0.9567901234567902)/300', 'T_mean + Rad*(0.9555555555555556)/300', 'T_mean + Rad*(0.9543209876543209)/300', 'T_mean + Rad*(0.9530864197530864)/300', 'T_mean + Rad*(0.9518518518518518)/300', 'T_mean + Rad*(0.9506172839506173)/300', 'T_mean + Rad*(0.9493827160493827)/300', 'T_mean + Rad*(0.9481481481481482)/300', 'T_mean + Rad*(0.9469135802469136)/300', 'T_mean + Rad*(0.945679012345679)/300', 'T_mean + Rad*(0.9444444444444444)/300', 'T_mean + Rad*(0.9432098765432099)/300', 'T_mean + Rad*(0.9419753086419753)/300', 'T_mean + Rad*(0.9407407407407408)/300', 'T_mean + Rad*(0.9395061728395062)/300', 'T_mean + Rad*(0.9382716049382716)/300', 'T_mean + Rad*(0.937037037037037)/300', 'T_mean + Rad*(0.9358024691358025)/300', 'T_mean + Rad*(0.9345679012345679)/300', 'T_mean + Rad*(0.9333333333333333)/300', 'T_mean + Rad*(0.9320987654320988)/300', 'T_mean + Rad*(0.9308641975308642)/300', 'T_mean + Rad*(0.9296296296296296)/300', 'T_mean + Rad*(0.928395061728395)/300', 'T_mean + Rad*(0.9271604938271605)/300', 'T_mean + Rad*(0.9259259259259259)/300', 'T_mean + Rad*(0.9246913580246914)/300', 'T_mean + Rad*(0.9234567901234568)/300', 'T_mean + Rad*(0.9222222222222222)/300', 'T_mean + Rad*(0.9209876543209876)/300', 'T_mean + Rad*(0.9197530864197531)/300', 'T_mean + Rad*(0.9185185185185185)/300', 'T_mean + Rad*(0.917283950617284)/300', 'T_mean + Rad*(0.9160493827160494)/300', 'T_mean + Rad*(0.9148148148148149)/300', 'T_mean + Rad*(0.9135802469135803)/300', 'T_mean + Rad*(0.9123456790123456)/300', 'T_mean + Rad*(0.9111111111111111)/300', 'T_mean + Rad*(0.9098765432098765)/300', 'T_mean + Rad*(0.908641975308642)/300', 'T_mean + Rad*(0.9074074074074074)/300', 'T_mean + Rad*(0.9061728395061728)/300', 'T_mean + Rad*(0.9049382716049382)/300', 'T_mean + Rad*(0.9037037037037037)/300', 'T_mean + Rad*(0.9024691358024691)/300', 'T_mean + Rad*(1.0071428571428571)/300', 'T_mean + Rad*(1.0059082892416227)/300', 'T_mean + Rad*(1.004673721340388)/300', 'T_mean + Rad*(1.0034391534391536)/300', 'T_mean + Rad*(1.002204585537919)/300', 'T_mean + Rad*(1.0009700176366843)/300', 'T_mean + Rad*(0.9997354497354497)/300', 'T_mean + Rad*(0.9985008818342151)/300', 'T_mean + Rad*(0.9972663139329806)/300', 'T_mean + Rad*(0.996031746031746)/300', 'T_mean + Rad*(0.9947971781305114)/300', 'T_mean + Rad*(0.9935626102292768)/300', 'T_mean + Rad*(0.9923280423280423)/300', 'T_mean + Rad*(0.9910934744268077)/300', 'T_mean + Rad*(0.9898589065255732)/300', 'T_mean + Rad*(0.9886243386243386)/300', 'T_mean + Rad*(0.9873897707231041)/300', 'T_mean + Rad*(0.9861552028218694)/300', 'T_mean + Rad*(0.9849206349206349)/300', 'T_mean + Rad*(0.9836860670194003)/300'], 'T_sparse_daytime': ['T_daytime_mean + Rad*(1.0)/300', 'T_daytime_mean + Rad*(0.9987654320987654)/300', 'T_daytime_mean + Rad*(0.9975308641975309)/300', 'T_daytime_mean + Rad*(0.9962962962962963)/300', 'T_daytime_mean + Rad*(0.9950617283950617)/300', 'T_daytime_mean + Rad*(0.9938271604938271)/300', 'T_daytime_mean + Rad*(0.9925925925925926)/300', 'T_daytime_mean + Rad*(0.991358024691358)/300', 'T_daytime_mean + Rad*(0.9901234567901235)/300', 'T_daytime_mean + Rad*(0.9888888888888889)/300', 'T_daytime_mean + Rad*(0.9876543209876543)/300', 'T_daytime_mean + Rad*(0.9864197530864197)/300', 'T_daytime_mean + Rad*(0.9851851851851852)/300', 'T_daytime_mean + Rad*(0.9839506172839506)/300', 'T_daytime_mean + Rad*(0.9827160493827161)/300', 'T_daytime_mean + Rad*(0.9814814814814815)/300', 'T_daytime_mean + Rad*(0.980246913580247)/300', 'T_daytime_mean + Rad*(0.9790123456790123)/300', 'T_daytime_mean + Rad*(0.9777777777777777)/300', 'T_daytime_mean + Rad*(0.9765432098765432)/300', 'T_daytime_mean + Rad*(0.9753086419753086)/300', 'T_daytime_mean + Rad*(0.9740740740740741)/300', 'T_daytime_mean + Rad*(0.9728395061728395)/300', 'T_daytime_mean + Rad*(0.971604938271605)/300', 'T_daytime_mean + Rad*(0.9703703703703703)/300', 'T_daytime_mean + Rad*(0.9691358024691358)/300', 'T_daytime_mean + Rad*(0.9679012345679012)/300', 'T_daytime_mean + Rad*(0.9666666666666667)/300', 'T_daytime_mean + Rad*(0.9654320987654321)/300', 'T_daytime_mean + Rad*(0.9641975308641976)/300', 'T_daytime_mean + Rad*(0.962962962962963)/300', 'T_daytime_mean + Rad*(0.9617283950617284)/300', 'T_daytime_mean + Rad*(0.9604938271604938)/300', 'T_daytime_mean + Rad*(0.9592592592592593)/300', 'T_daytime_mean + Rad*(0.9580246913580247)/300', 'T_daytime_mean + Rad*(0.9567901234567902)/300', 'T_daytime_mean + Rad*(0.9555555555555556)/300', 'T_daytime_mean + Rad*(0.9543209876543209)/300', 'T_daytime_mean + Rad*(0.9530864197530864)/300', 'T_daytime_mean + Rad*(0.9518518518518518)/300', 'T_daytime_mean + Rad*(0.9506172839506173)/300', 'T_daytime_mean + Rad*(0.9493827160493827)/300', 'T_daytime_mean + Rad*(0.9481481481481482)/300', 'T_daytime_mean + Rad*(0.9469135802469136)/300', 'T_daytime_mean + Rad*(0.945679012345679)/300', 'T_daytime_mean + Rad*(0.9444444444444444)/300', 'T_daytime_mean + Rad*(0.9432098765432099)/300', 'T_daytime_mean + Rad*(0.9419753086419753)/300', 'T_daytime_mean + Rad*(0.9407407407407408)/300', 'T_daytime_mean + Rad*(0.9395061728395062)/300', 'T_daytime_mean + Rad*(0.9382716049382716)/300', 'T_daytime_mean + Rad*(0.937037037037037)/300', 'T_daytime_mean + Rad*(0.9358024691358025)/300', 'T_daytime_mean + Rad*(0.9345679012345679)/300', 'T_daytime_mean + Rad*(0.9333333333333333)/300', 'T_daytime_mean + Rad*(0.9320987654320988)/300', 'T_daytime_mean + Rad*(0.9308641975308642)/300', 'T_daytime_mean + Rad*(0.9296296296296296)/300', 'T_daytime_mean + Rad*(0.928395061728395)/300', 'T_daytime_mean + Rad*(0.9271604938271605)/300', 'T_daytime_mean + Rad*(0.9259259259259259)/300', 'T_daytime_mean + Rad*(0.9246913580246914)/300', 'T_daytime_mean + Rad*(0.9234567901234568)/300', 'T_daytime_mean + Rad*(0.9222222222222222)/300', 'T_daytime_mean + Rad*(0.9209876543209876)/300', 'T_daytime_mean + Rad*(0.9197530864197531)/300', 'T_daytime_mean + Rad*(0.9185185185185185)/300', 'T_daytime_mean + Rad*(0.917283950617284)/300', 'T_daytime_mean + Rad*(0.9160493827160494)/300', 'T_daytime_mean + Rad*(0.9148148148148149)/300', 'T_daytime_mean + Rad*(0.9135802469135803)/300', 'T_daytime_mean + Rad*(0.9123456790123456)/300', 'T_daytime_mean + Rad*(0.9111111111111111)/300', 'T_daytime_mean + Rad*(0.9098765432098765)/300', 'T_daytime_mean + Rad*(0.908641975308642)/300', 'T_daytime_mean + Rad*(0.9074074074074074)/300', 'T_daytime_mean + Rad*(0.9061728395061728)/300', 'T_daytime_mean + Rad*(0.9049382716049382)/300', 'T_daytime_mean + Rad*(0.9037037037037037)/300', 'T_daytime_mean + Rad*(0.9024691358024691)/300', 'T_daytime_mean + Rad*(1.0071428571428571)/300', 'T_daytime_mean + Rad*(1.0059082892416227)/300', 'T_daytime_mean + Rad*(1.004673721340388)/300', 'T_daytime_mean + Rad*(1.0034391534391536)/300', 'T_daytime_mean + Rad*(1.002204585537919)/300', 'T_daytime_mean + Rad*(1.0009700176366843)/300', 'T_daytime_mean + Rad*(0.9997354497354497)/300', 'T_daytime_mean + Rad*(0.9985008818342151)/300', 'T_daytime_mean + Rad*(0.9972663139329806)/300', 'T_daytime_mean + Rad*(0.996031746031746)/300', 'T_daytime_mean + Rad*(0.9947971781305114)/300', 'T_daytime_mean + Rad*(0.9935626102292768)/300', 'T_daytime_mean + Rad*(0.9923280423280423)/300', 'T_daytime_mean + Rad*(0.9910934744268077)/300', 'T_daytime_mean + Rad*(0.9898589065255732)/300', 'T_daytime_mean + Rad*(0.9886243386243386)/300', 'T_daytime_mean + Rad*(0.9873897707231041)/300', 'T_daytime_mean + Rad*(0.9861552028218694)/300', 'T_daytime_mean + Rad*(0.9849206349206349)/300', 'T_daytime_mean + Rad*(0.9836860670194003)/300']}
LIST_NAMES = sorted(ALGEBRAIC_LIST_SPECS.keys())
LIST_SIZE = min(len(values) for values in ALGEBRAIC_LIST_SPECS.values()) if ALGEBRAIC_LIST_SPECS else 0

_NORMALIZED_CACHE: dict[str, str] = {}
_COMPILED_CACHE: dict[str, object] = {}


def _default_input_value(name: str) -> float:
    lower = name.lower()
    if lower in {"rad", "radiation", "solar_radiation", "ppfd"} or "rad" in lower:
        return 300.0
    if lower.startswith("t_") or "temp" in lower or lower in {"t", "tin", "t_in", "tmean", "t_mean"}:
        return 20.0
    return 0.0



def _normalize_expr(expr: str) -> str:
    cached = _NORMALIZED_CACHE.get(expr)
    if cached is not None:
        return cached

    normalized = str(expr).strip()
    normalized = re.sub(r"\btrue\b", "True", normalized)
    normalized = re.sub(r"\bfalse\b", "False", normalized)
    normalized = normalized.replace("^", "**")
    _NORMALIZED_CACHE[expr] = normalized
    return normalized



def _safe_eval(expr: str, env: dict[str, Any]) -> float:
    code = _COMPILED_CACHE.get(expr)
    if code is None:
        code = compile(_normalize_expr(expr), "<algebraic-input-expr>", "eval")
        _COMPILED_CACHE[expr] = code

    safe_globals = {
        "__builtins__": {},
        "math": math,
        "pow": pow,
        "max": max,
        "min": min,
        "abs": abs,
        "exp": math.exp,
        "log": math.log,
        "ln": math.log,
    }
    return float(eval(code, safe_globals, env))


class GreenhouseInputModule:
    def __init__(
        self,
        name: str = MODULE_NAME,
        limit: int | None = None,
        hours: int = 48,
        **input_series,
    ) -> None:
        if hours <= 0:
            raise ValueError("hours must be greater than zero")
        if LIST_SIZE <= 0:
            raise ValueError(f"No algebraic lists were generated for {TEMPLATE_NAME}")

        self.name = name
        self.limit = LIST_SIZE if limit is None else min(int(limit), LIST_SIZE)
        if self.limit <= 0:
            raise ValueError("limit must be greater than zero")

        self.hours = int(hours)
        self.current_timestep = 0
        self.data_size = self.hours
        self.input_series = {
            input_name: self._normalize_series(
                input_series.get(input_name, _default_input_value(input_name)),
                self.hours,
            )
            for input_name in INPUT_NAMES
        }

    @staticmethod
    def _normalize_series(value: float | Iterable[float], hours: int) -> list[float]:
        if isinstance(value, (int, float)):
            return [float(value) for _ in range(hours)]

        values = [float(item) for item in value]
        if len(values) < hours:
            raise ValueError("Input time series must contain at least 'hours' values")
        return values[:hours]

    def get_variable_names(self):
        names = list(INPUT_NAMES)
        for index in range(self.limit):
            for list_name in LIST_NAMES:
                names.append(f"{list_name}_{index}")
        return names

    def _env_for_step(self, step: int) -> dict[str, float]:
        return {
            input_name: values[step]
            for input_name, values in self.input_series.items()
        }

    def get_variables(self):
        if self.current_timestep >= self.data_size:
            return None

        step = self.current_timestep
        env = self._env_for_step(step)
        values = dict(env)

        for index in range(self.limit):
            for list_name in LIST_NAMES:
                expr = ALGEBRAIC_LIST_SPECS[list_name][index]
                values[f"{list_name}_{index}"] = _safe_eval(expr, env)

        return values

    def step(self):
        self.current_timestep += 1
        return self.current_timestep

    def reset(self):
        self.current_timestep = 0

    def read_input(self, input=None, *args):
        return None

    def closeFile(self):
        return None

    def assignHeader(self, header):
        return None


def create_input_module(name: str = MODULE_NAME, limit: int | None = None, hours: int = 48, **input_series) -> GreenhouseInputModule:
    return GreenhouseInputModule(name=name, limit=limit, hours=hours, **input_series)
