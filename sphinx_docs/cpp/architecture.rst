C++ Firmware Architecture
=========================

Overview
--------

The microsync firmware is built on the Arduino Due platform using the SAM3X8E ARM Cortex-M3 microcontroller. The firmware provides microsecond-precision timing control for microscope synchronization with a focus on safety, reliability, and performance.

System Architecture
-------------------

.. image:: ../../doc/system_arch_diagram.drawio.svg
   :alt: System architecture diagram
   :align: center
   :width: 100%

Color legend: green – software components, yellow – microcontroller peripherals, purple – external hardware.

Core Components
---------------

Event System
^^^^^^^^^^^^

The heart of the synchronization system is the priority queue-based event scheduler:

- **Priority Queue**: Orders events by timestamp for precise execution
- **Event Processing**: Handles up to 450 scheduled events
- **Microsecond Precision**: 64-bit timestamp system with overflow handling
- **Real-time Execution**: Interrupt-driven event processing

.. code-block:: cpp

   // Event structure for priority queue
   struct Event {
       uint8_t func;           // Function to execute
       uint8_t arg1, arg2;     // Function arguments
       uint64_t ts64_cts;      // 64-bit timestamp in clock ticks
       uint16_t N;             // Number of repetitions
       uint32_t interv_cts;    // Interval between repetitions
   };

Communication System
^^^^^^^^^^^^^^^^^^^^

UART-based communication protocol for host-device interaction:

- **Baud Rate**: 115,200 bps
- **Protocol**: Command-response with error handling
- **Buffer Management**: Ring buffer with overflow protection
- **Timeout Handling**: Automatic detection of incomplete transmissions

.. code-block:: cpp

   // UART communication functions
   void init_uart_comm(void);
   void uart_tx(const char* data, uint16_t len);
   void process_uart_rx(void);

Safety Systems
^^^^^^^^^^^^^^

Laser safety interlock system with hardware and software protection:

- **Hardware Interlock**: D12/D13 circuit monitoring
- **Software Timer**: 1.56ms heartbeat generation
- **Automatic Shutdown**: Disables lasers on interlock failure
- **Runtime Control**: Enable/disable via software

.. code-block:: cpp

   // Interlock control functions
   void init_interlock(void);
   void enable_lasers(void);
   void disable_lasers(void);

Hardware Interface
^^^^^^^^^^^^^^^^^^

Pin management and hardware abstraction layer:

- **Pin Mapping**: Arduino Due pin assignments
- **Laser Shutters**: D8 (Cy2), D9 (Cy3), D10 (Cy5), D11 (Cy7) - see ``globals.h``
- **Camera Trigger**: D7 - see ``globals.h``
- **Status LEDs**: Visual feedback and debugging

.. code-block:: cpp

   // Pin control functions
   void init_pins(void);
   void set_pin(uint8_t pin, bool state);
   void toggle_pin(uint8_t pin);

Memory Management
-----------------

Optimized memory usage for embedded constraints:

- **Static Allocation**: Pre-allocated buffers and structures
- **Stack Management**: Careful stack usage monitoring
- **Heap Protection**: Out-of-memory handler with error reporting
- **Buffer Sizes**: Optimized for typical use cases

.. code-block:: cpp

   // Memory management
   #define MAX_N_EVENTS 450
   #define UART_BUFFER_SIZE 256
   #define WATCHDOG_TIMEOUT 1000  // ms

Error Handling
--------------

Comprehensive error detection and recovery:

- **Watchdog Timer**: System reset on software hang
- **Hard Fault Handler**: Graceful handling of hardware errors
- **UART Error Reporting**: Real-time error communication
- **LED Status**: Visual error indication

.. code-block:: cpp

   // Error handling functions
   void activate_watchdog(void);
   void err_led_on(void);
   void out_of_memory_handler(void);

Performance Characteristics
---------------------------

- **Event Scheduling**: Up to 450 events
- **Timing Precision**: Microsecond accuracy
- **Response Time**: < 1ms command processing
- **Memory Usage**: < 32KB RAM
- **CPU Utilization**: < 10% typical load

Build System
------------

The firmware is built using Microchip Studio with the following configuration:

- **Target**: Arduino Due (SAM3X8E)
- **Compiler**: ARM GCC
- **Optimization**: -O2 for performance
- **Debugging**: Full debug symbols in Debug build
- **Release**: Optimized for production use 