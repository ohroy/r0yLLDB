import lldb
import fbchisellldbbase as fb
from typing import cast
import threading

debugger = cast(lldb.SBDebugger, lldb.debugger)


def lldbcommands():
    return [ListenModuleWithOffset()]


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


class ListenModuleWithOffset(fb.FBCommand):
    def name(self) -> str:  # type: ignore
        return "lmo"

    def description(self) -> str:  # type: ignore
        return "listen module load and set breakpoint with offset"

    def args(self):
        return [
            fb.FBCommandArgument(
                arg="module",
                type="str",
                help="the module name",
            ),
            fb.FBCommandArgument(
                arg="offset",
                type="string",
                help="the offset with hex format",
            ),
        ]

    def run(self, arguments, option):
        target: lldb.SBTarget = lldb.debugger.GetSelectedTarget()  # type: lldb.SBTarget
        broadcaster: lldb.SBBroadcaster = target.GetBroadcaster()
        # Create an empty event object.
        event = lldb.SBEvent()
        listener = lldb.SBListener("my listener")
        broadcaster.AddListener(listener, lldb.SBTarget.eBroadcastBitModulesLoaded)
        traceOn = True

        class MyListeningThread(threading.Thread):
            def run(self):
                count = 0
                # Let's only try at most 4 times to retrieve any kind of event.
                # After that, the thread exits.
                while True:
                    if traceOn:
                        print("Try wait for event...")
                    if listener.WaitForEventForBroadcasterWithType(
                        5, broadcaster, lldb.SBTarget.eBroadcastBitModulesLoaded, event
                    ):
                        if traceOn:
                            num_modules = lldb.SBTarget.GetNumModulesFromEvent(event)
                            module: lldb.SBModule = (
                                lldb.SBTarget.GetModuleAtIndexFromEvent(
                                    num_modules - 1, event
                                )
                            )  # type: lldb.SBModule
                            spec: lldb.SBFileSpec = module.GetFileSpec()
                            filename: str = spec.GetFilename()
                            print(f"加载模块: {module.GetFileSpec()}")
                            if filename == arguments[0]:
                                print(f"目标模块已加载，设置断点...")
                                set_breakpoint(target, module, int(arguments[1], 16))
                                break
                    else:
                        if traceOn:
                            print("timeout occurred waiting for event...")
                    count = count + 1
                return

        my_thread = MyListeningThread()
        my_thread.start()
        # my_thread.join()
