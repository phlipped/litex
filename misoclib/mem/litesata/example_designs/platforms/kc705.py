from mibuild.generic_platform import *
from mibuild.crg import SimpleCRG
from mibuild.xilinx.common import CRG_DS
from mibuild.xilinx.ise import XilinxISEPlatform
from mibuild.xilinx.vivado import XilinxVivadoPlatform
from mibuild.xilinx.programmer import *

_io = [
	("user_led", 0, Pins("AB8"), IOStandard("LVCMOS15")),
	("user_led", 1, Pins("AA8"), IOStandard("LVCMOS15")),
	("user_led", 2, Pins("AC9"), IOStandard("LVCMOS15")),
	("user_led", 3, Pins("AB9"), IOStandard("LVCMOS15")),
	("user_led", 4, Pins("AE26"), IOStandard("LVCMOS25")),
	("user_led", 5, Pins("G19"), IOStandard("LVCMOS25")),
	("user_led", 6, Pins("E18"), IOStandard("LVCMOS25")),
	("user_led", 7, Pins("F16"), IOStandard("LVCMOS25")),

	("cpu_reset", 0, Pins("AB7"), IOStandard("LVCMOS15")),

	("clk200", 0,
		Subsignal("p", Pins("AD12"), IOStandard("LVDS")),
		Subsignal("n", Pins("AD11"), IOStandard("LVDS"))
	),

	("clk156", 0,
		Subsignal("p", Pins("K28"), IOStandard("LVDS_25")),
		Subsignal("n", Pins("K29"), IOStandard("LVDS_25"))
	),


	("serial", 0,
		Subsignal("cts", Pins("L27")),
		Subsignal("rts", Pins("K23")),
		Subsignal("tx", Pins("K24")),
		Subsignal("rx", Pins("M19")),
		IOStandard("LVCMOS25")
	),

	("sata", 0,
		Subsignal("refclk_p", Pins("C8")),
		Subsignal("refclk_n", Pins("C7")),
		Subsignal("txp", Pins("D2")),
		Subsignal("txn", Pins("D1")),
		Subsignal("rxp", Pins("E4")),
		Subsignal("rxn", Pins("E3")),
	),
]

def Platform(*args, toolchain="vivado", programmer="xc3sprog", **kwargs):
	if toolchain == "ise":
		xilinx_platform = XilinxISEPlatform
	elif toolchain == "vivado":
		xilinx_platform = XilinxVivadoPlatform
	else:
		raise ValueError

	class RealPlatform(xilinx_platform):
		bitgen_opt = "-g LCK_cycle:6 -g Binary:Yes -w -g ConfigRate:12 -g SPI_buswidth:4"

		def __init__(self, crg_factory=lambda p: CRG_DS(p, "clk200", "cpu_reset")):
			xilinx_platform.__init__(self, "xc7k325t-ffg900-2", _io, crg_factory)

		def create_programmer(self):
			if programmer == "xc3sprog":
				return XC3SProg("jtaghs1_fast", "bscan_spi_kc705.bit")
			elif programmer == "vivado":
				return VivadoProgrammer()
			else:
				raise ValueError

		def do_finalize(self, fragment):
			try:
				self.add_period_constraint(self.lookup_request("clk156").p, 6.4)
			except ConstraintError:
				pass
			try:
				self.add_period_constraint(self.lookup_request("clk200").p, 5.0)
			except ConstraintError:
				pass
			try:
				self.add_period_constraint(self.lookup_request("sata_host").refclk_p, 6.66)
			except ConstraintError:
				pass
			self.add_platform_command("""
create_clock -name sys_clk -period 6 [get_nets sys_clk]
create_clock -name sata_rx_clk -period 3.33 [get_nets sata_rx_clk]
create_clock -name sata_tx_clk -period 3.33 [get_nets sata_tx_clk]

set_false_path -from [get_clocks sys_clk] -to [get_clocks sata_rx_clk]
set_false_path -from [get_clocks sys_clk] -to [get_clocks sata_tx_clk]
set_false_path -from [get_clocks sata_rx_clk] -to [get_clocks sys_clk]
set_false_path -from [get_clocks sata_tx_clk] -to [get_clocks sys_clk]

set_property CFGBVS VCCO [current_design]
set_property CONFIG_VOLTAGE 2.5 [current_design]
""")

	return RealPlatform(*args, **kwargs)