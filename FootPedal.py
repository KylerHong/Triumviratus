    import board
    import busio
    import digitalio
    import RPi.GPIO
    import adafruit_mcp3xxx.mcp3008 as MCP
    from adafruit_mcp3xxx.analog_in import AnalogIn
    SPI = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
    MCP3008_CS = digitalio.DigitalInOut(board.D22)
    mcp = MCP.MCP3008(SPI, MCP3008_CS)
    foot_axis = AnalogIn(mcp, MCP.P0)
    
    
    print(foot_axis.voltage)