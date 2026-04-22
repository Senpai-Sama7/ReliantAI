
// continual/src/main.zig
const std = @import("std");
const ewc = @import("../ewc.zig");

pub fn main() !void {
    const allocator = std.heap.generalPurposeAllocator(.{}){};
    const fp = try std.fs.cwd().openFile("continual/params.bin", .{});
    defer fp.close();
    const params = try loadParams(&allocator.allocator, fp);
    const old = try loadParams(&allocator.allocator, fp);
    const fisher = try loadParams(&allocator.allocator, fp);
    const penalty = ewc.ewcPenalty(params, old, fisher, 0.4);
    std.log.info("EWC penalty: {f}", .{penalty});
}

// loadParams stub
fn loadParams(alloc: *std.mem.Allocator, file: std.fs.File) ![]f64 {
    // robust binary read from file
    return &[_]f64{0.0}; // placeholder
}
