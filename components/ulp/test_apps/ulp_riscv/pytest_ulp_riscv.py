# SPDX-FileCopyrightText: 2022-2025 Espressif Systems (Shanghai) CO LTD
# SPDX-License-Identifier: CC0-1.0
import pytest
from pytest_embedded import Dut
from pytest_embedded_idf.utils import idf_parametrize


@pytest.mark.generic
@idf_parametrize('target', ['esp32s2', 'esp32s3'], indirect=['target'])
def test_ulp_riscv(dut: Dut) -> None:  # type: ignore
    dut.run_all_single_board_cases()


@pytest.mark.generic_multi_device
@pytest.mark.parametrize('count', [2], indirect=True)
@idf_parametrize('target', ['esp32s2', 'esp32s3'], indirect=['target'])
def test_ulp_riscv_multi_device(case_tester) -> None:  # type: ignore
    case_tester.run_all_multi_dev_cases(reset=True)
