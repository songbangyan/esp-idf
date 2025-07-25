Camera Controller Driver
========================

:link_to_translation:`zh_CN:[中文]`

Introduction
------------

{IDF_TARGET_NAME} has the following hardware that is intended for communication with external camera sensor:

.. list::

    : SOC_MIPI_CSI_SUPPORTED : - MIPI Camera Serial Interface (MIPI CSI)
    : SOC_ISP_DVP_SUPPORTED : - Digital Video Port through ISP module (ISP DVP)
    : SOC_LCDCAM_CAM_SUPPORTED : - Digital Video Port through LCD_CAM module(LCD_CAM DVP)

The camera controller driver is designed for this hardware peripheral.


Functional Overview
-------------------

.. list::

    - :ref:`cam-resource-allocation` - covers how to allocate camera controller instances with properly set of configurations. It also covers how to recycle the resources when they are no longer needed.
    - :ref:`cam-enable-disable` - covers how to enable and disable a camera controller.
    - :ref:`cam-start-stop` - covers how to start and stop a camera controller.
    - :ref:`cam-receive`- covers how to receive camera signal from a sensor or something else.
    - :ref:`cam-callback`- covers how to hook user specific code to camera controller driver event callback function.
    - :ref:`cam-thread-safety` - lists which APIs are guaranteed to be thread safe by the driver.
    - :ref:`cam-kconfig-options` - lists the supported Kconfig options that can bring different effects to the driver.
    - :ref:`cam-iram-safe` - describes tips on how to make the CSI interrupt and control functions work better along with a disabled cache.

.. _cam-resource-allocation:

Resource Allocation
^^^^^^^^^^^^^^^^^^^

Install Camera Controller Driver
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Camera controller driver can be implemented in one of following ways:

.. list::

    : SOC_MIPI_CSI_SUPPORTED : - :cpp:func:`esp_cam_new_csi_ctlr`
    : SOC_ISP_DVP_SUPPORTED : - :cpp:func:`esp_cam_new_isp_dvp_ctlr`
    : SOC_LCDCAM_CAM_SUPPORTED : - :cpp:func:`esp_cam_new_lcd_cam_ctlr`

.. only:: SOC_MIPI_CSI_SUPPORTED

    A camera controller driver can be implemented by the CSI peripheral, which requires the configuration that specified by :cpp:type:`esp_cam_ctlr_csi_config_t`.

    If the configurations in :cpp:type:`esp_cam_ctlr_csi_config_t` is specified, users can call :cpp:func:`esp_cam_new_csi_ctlr` to allocate and initialize a CSI camera controller handle. This function will return an CSI camera controller handle if it runs correctly. You can take following code as reference.

    .. code:: c

        esp_cam_ctlr_csi_config_t csi_config = {
            .ctlr_id = 0,
            .h_res = MIPI_CSI_DISP_HSIZE,
            .v_res = MIPI_CSI_DISP_VSIZE_640P,
            .lane_bit_rate_mbps = MIPI_CSI_LANE_BITRATE_MBPS,
            .input_data_color_type = CAM_CTLR_COLOR_RAW8,
            .output_data_color_type = CAM_CTLR_COLOR_RGB565,
            .data_lane_num = 2,
            .byte_swap_en = false,
            .queue_items = 1,
        };
        esp_cam_ctlr_handle_t handle = NULL;
        ESP_ERROR_CHECK(esp_cam_new_csi_ctlr(&csi_config, &handle));

.. only:: SOC_ISP_DVP_SUPPORTED

    A camera controller driver can be implemented by the ISP DVP peripheral, which requires the configuration that specified by :cpp:type:`esp_cam_ctlr_isp_dvp_cfg_t`.

    If the configurations in :cpp:type:`esp_cam_ctlr_isp_dvp_cfg_t` is specified, users can call :cpp:func:`esp_cam_new_isp_dvp_ctlr` to allocate and initialize a ISP DVP camera controller handle. This function will return an ISP DVP camera controller handle if it runs correctly. You can take following code as reference.

    Before calling :cpp:func:`esp_cam_new_isp_dvp_ctlr`, you should also call :cpp:func:`esp_isp_new_processor` to create an ISP handle.

    .. code:: c

        isp_proc_handle_t isp_proc = NULL;
        esp_isp_processor_cfg_t isp_config = {
            .clk_hz = 120 * 1000 * 1000,
            .input_data_source = ISP_INPUT_DATA_SOURCE_DVP,
            .input_data_color_type = ISP_COLOR_RAW8,
            .output_data_color_type = ISP_COLOR_RGB565,
            .has_line_start_packet = false,
            .has_line_end_packet = false,
            .h_res = MIPI_CSI_DISP_HSIZE,
            .v_res = MIPI_CSI_DISP_VSIZE,
        };
        ESP_ERROR_CHECK(esp_isp_new_processor(&isp_config, &isp_proc));

        esp_cam_ctlr_isp_dvp_cfg_t dvp_ctlr_config = {
            .data_width = 8,
            .data_io = {53, 54, 52, 0, 1, 45, 46, 47, -1, -1, -1, -1, -1, -1, -1, -1},
            .pclk_io = 21,
            .hsync_io = 5,
            .vsync_io = 23,
            .de_io = 22,
            .io_flags.vsync_invert = 1,
            .queue_items = 10,
        };
        ESP_ERROR_CHECK(esp_cam_new_isp_dvp_ctlr(isp_proc, &dvp_ctlr_config, &cam_handle));

.. only:: SOC_LCDCAM_CAM_SUPPORTED

    A camera controller driver can be implemented by the DVP port of LCD_CAM, which requires the configuration that specified by :cpp:type:`esp_cam_ctlr_dvp_config_t`.

    :cpp:member:`esp_cam_ctlr_dvp_config_t::exexternal_xtal`: set this to use externally generated xclk, otherwise the camera driver will generate it internally.

    If :cpp:type:`esp_cam_ctlr_lcd_cam_cfg_t` is specified, users can call :cpp:func:`esp_cam_new_lcd_cam_ctlr` to allocate and initialize a DVP camera controller handle. This function will return an DVP camera controller handle if it runs correctly. You can take following code as reference.

    After calling :cpp:func:`esp_cam_new_dvp_ctlr`, you should allocate a camera buffer that meets the alignment constraints, or call :cpp:func:`esp_cam_ctlr_alloc_buffer` to automatically allocate.

    .. code:: c

        esp_cam_ctlr_handle_t cam_handle = NULL;
        esp_cam_ctlr_dvp_pin_config_t pin_cfg = {
            .data_width = EXAMPLE_DVP_CAM_DATA_WIDTH,
            .data_io = {
                EXAMPLE_DVP_CAM_D0_IO,
                EXAMPLE_DVP_CAM_D1_IO,
                EXAMPLE_DVP_CAM_D2_IO,
                EXAMPLE_DVP_CAM_D3_IO,
                EXAMPLE_DVP_CAM_D4_IO,
                EXAMPLE_DVP_CAM_D5_IO,
                EXAMPLE_DVP_CAM_D6_IO,
                EXAMPLE_DVP_CAM_D7_IO,
            },
            .vsync_io = EXAMPLE_DVP_CAM_VSYNC_IO,
            .de_io = EXAMPLE_DVP_CAM_DE_IO,
            .pclk_io = EXAMPLE_DVP_CAM_PCLK_IO,
            .xclk_io = EXAMPLE_DVP_CAM_XCLK_IO, // Set XCLK pin to generate XCLK signal
        };
        esp_cam_ctlr_dvp_config_t dvp_config = {
            .ctlr_id = 0,
            .clk_src = CAM_CLK_SRC_DEFAULT,
            .h_res = CONFIG_EXAMPLE_CAM_HRES,
            .v_res = CONFIG_EXAMPLE_CAM_VRES,
            .input_data_color_type = CAM_CTLR_COLOR_RGB565,
            .dma_burst_size = 128,
            .pin = &pin_cfg,
            .bk_buffer_dis = 1,
            .xclk_freq = EXAMPLE_DVP_CAM_XCLK_FREQ_HZ,
        };

        ESP_ERROR_CHECK(esp_cam_new_dvp_ctlr(&dvp_config, &cam_handle));

Uninstall Camera Controller Driver
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If a previously installed camera controller driver is no longer needed, it's recommended to recycle the resource by calling :cpp:func:`esp_cam_ctlr_del`, so that to release the underlying hardware.

.. _cam-enable-disable:

Enable and Disable Camera Controller Driver
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Before starting camera controller operation, you need to enable the camera controller driver first, by calling :cpp:func:`esp_cam_ctlr_enable`. This function:

* Switches the driver state from **init** to **enable**.

.. code:: c

    ESP_ERROR_CHECK(esp_cam_ctlr_enable(handle));

Calling :cpp:func:`esp_cam_ctlr_disable` does the opposite, that is, put the driver back to the **init** state.

.. code:: c

    ESP_ERROR_CHECK(esp_cam_ctlr_disable(handle));

.. _cam-start-stop:

Start and Stop Camera Controller Driver
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Before receiving camera signal from camera sensor, you need to start the camera controller driver first, by calling :cpp:func:`esp_cam_ctlr_start`. This function:

* Switches the driver state from **enable** to **start**.

.. code:: c

    ESP_ERROR_CHECK(esp_cam_ctlr_start(handle));

Calling :cpp:func:`esp_cam_ctlr_stop` does the opposite, that is, put the driver back to the **enable** state.

.. code:: c

    ESP_ERROR_CHECK(esp_cam_ctlr_stop(handle));

.. _cam-receive:

Receive from a Camera Sensor
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Now you can call :cpp:func:`esp_cam_ctlr_receive` to receive from a camera sensor or something else.

.. code:: c

    ESP_ERROR_CHECK(esp_cam_ctlr_receive(handle, &my_trans, ESP_CAM_CTLR_MAX_DELAY));

.. _cam-callback:

Register Event Callbacks
^^^^^^^^^^^^^^^^^^^^^^^^

After the camera controller driver starts receiving, it can generate a specific event dynamically. If you have some functions that should be called when the event happens, please hook your function to the interrupt service routine by calling :cpp:func:`esp_cam_ctlr_register_event_callbacks`. All supported event callbacks are listed in :cpp:type:`esp_cam_ctlr_evt_cbs_t`:

- :cpp:member:`esp_cam_ctlr_evt_cbs_t::on_get_new_trans` sets a callback function which will be called after the camera controller driver finishes previous transaction, and tries to get a new transaction descriptor. It will also be called when in :cpp:func:`s_ctlr_csi_start`. If this callback does not get a new transaction descriptor, the camera controller driver will use the internal backup buffer if ``bk_buffer_dis`` flag is set.

- :cpp:member:`esp_cam_ctlr_evt_cbs_t::on_trans_finished` sets a callback function when the camera controller driver finishes a transaction. As this function is called within the ISR context, you must ensure that the function does not attempt to block (e.g., by making sure that only FreeRTOS APIs with ``ISR`` suffix are called from within the function).

.. _cam-thread-safety:

Thread Safety
^^^^^^^^^^^^^

The factory functions:

.. list::

    :SOC_MIPI_CSI_SUPPORTED: - :cpp:func:`esp_cam_new_csi_ctlr`
    :SOC_ISP_DVP_SUPPORTED: - :cpp:func:`esp_cam_new_isp_dvp_ctlr`
    - :cpp:func:`esp_cam_ctlr_del`

    are guaranteed to be thread safe by the driver, which means, they can be called from different RTOS tasks without protection by extra locks.

.. _cam-kconfig-options:

Kconfig Options
^^^^^^^^^^^^^^^

The following Kconfig options affect the behavior of the interrupt handler when cache is disabled:

.. list::

    :SOC_MIPI_CSI_SUPPORTED: - :ref:`CONFIG_CAM_CTLR_MIPI_CSI_ISR_CACHE_SAFE`, see :ref:`cam-thread-safety` for more details.
    :SOC_ISP_DVP_SUPPORTED: - :ref:`CONFIG_CAM_CTLR_ISP_DVP_ISR_CACHE_SAFE`, see :ref:`cam-thread-safety` for more details.

.. _cam-iram-safe:

IRAM Safe
^^^^^^^^^

By default, the CSI interrupt will be deferred when the cache is disabled because of writing or erasing the flash.

There are Kconfig options

.. list::

    :SOC_MIPI_CSI_SUPPORTED: - :ref:`CONFIG_CAM_CTLR_MIPI_CSI_ISR_CACHE_SAFE`
    :SOC_ISP_DVP_SUPPORTED: - :ref:`CONFIG_CAM_CTLR_ISP_DVP_ISR_CACHE_SAFE`

that

-  Enables the interrupt being serviced even when the cache is disabled
-  Places all functions that used by the ISR into IRAM
-  Places driver object into DRAM (in case it is mapped to PSRAM by accident)

This allows the interrupt to run while the cache is disabled, but comes at the cost of increased IRAM consumption. So user callbacks need to notice that the code and data inside (the callback) should be IRAM-safe or DRAM-safe, when cache is disabled.

Application Examples
--------------------

* :example:`peripherals/camera/mipi_isp_dsi` demonstrates how to use the ``esp_driver_cam`` component to capture signals from a MIPI CSI camera sensor via the ISP module and display it on a LCD screen via a DSI interface.
* :example:`peripherals/camera/dvp_isp_dsi` demonstrates how to use the ``esp_driver_cam`` component to capture signals from a DVP camera sensor via the ISP module and display it on a LCD screen via a DSI interface.

API Reference
-------------

.. include-build-file:: inc/esp_cam_ctlr.inc
.. include-build-file:: inc/esp_cam_ctlr_types.inc
.. include-build-file:: inc/esp_cam_ctlr_csi.inc
.. include-build-file:: inc/esp_cam_ctlr_isp_dvp.inc
