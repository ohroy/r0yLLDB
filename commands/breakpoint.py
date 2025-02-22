import lldb
import fbchisellldbbase as fb
from typing import cast
import threading

debugger = cast(lldb.SBDebugger, lldb.debugger)


def lldbcommands():
    return [BreakPointCurrentOffset(), BreakPointCurrentOffset()]


def set_breakpoint(target: lldb.SBTarget, module: lldb.SBModule, offset: int):
    """在指定模块 + 偏移处设置断点"""
    file_header_addr = module.GetObjectFileHeaderAddress()  # type: lldb.SBAddress
    base_addr = file_header_addr.GetLoadAddress(target)
    if base_addr == lldb.LLDB_INVALID_ADDRESS:
        print(f"无法获取模块基地址")
        return

    breakpoint_addr = base_addr + offset
    print(f"在 {target} 的 {hex(breakpoint_addr)} 处设置断点")

    bp = target.BreakpointCreateByAddress(breakpoint_addr)
    if bp.IsValid():
        print(f"断点设置成功: {bp}")
    else:
        print(f"断点设置失败")


class BreakPointCurrentOffset(fb.FBCommand):
    """在当前模块 + 偏移处设置断点"""

    def name(self) -> str:  # type: ignore
        return "bo"

    def description(self) -> str:  # type: ignore
        return "listen module load and set breakpoint with offset"

    def args(self):
        return [
            fb.FBCommandArgument(
                arg="offset",
                type="string",
                help="the offset with hex format",
            ),
        ]

    def run(self, arguments, option):
        target: lldb.SBTarget = lldb.debugger.GetSelectedTarget()  # type: lldb.SBTarget
        process: lldb.SBProcess = target.GetProcess()
        thread: lldb.SBThread = process.GetSelectedThread()
        frame: lldb.SBFrame =  thread.GetFrameAtIndex(0)
        module: lldb.SBModule = frame.GetModule()
        set_breakpoint(target, module, int(arguments[0], 16))
