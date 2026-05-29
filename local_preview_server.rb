require "webrick"
require "pathname"

ROOT = Pathname.new(__dir__).realpath
PORT = 4000

server = WEBrick::HTTPServer.new(
  Port: PORT,
  BindAddress: "127.0.0.1",
  AccessLog: [],
  Logger: WEBrick::Log.new($stderr, WEBrick::Log::WARN)
)

server.mount_proc "/" do |req, res|
  path = req.path
  relative =
    if path == "/"
      "index.html"
    elsif path.start_with?("/imsi/")
      path.delete_prefix("/imsi/")
    else
      path.sub(%r{\A/}, "")
    end

  target = ROOT.join(relative).cleanpath

  unless target.to_s.start_with?(ROOT.to_s) && target.exist?
    res.status = 404
    res["Content-Type"] = "text/plain; charset=utf-8"
    res.body = "Not Found"
    next
  end

  target = target.join("index.html") if target.directory?

  unless target.exist? && target.file?
    res.status = 404
    res["Content-Type"] = "text/plain; charset=utf-8"
    res.body = "Not Found"
    next
  end

  res.status = 200
  res["Cache-Control"] = "no-store"
  res["Content-Type"] = WEBrick::HTTPUtils.mime_type(target.extname, WEBrick::HTTPUtils::DefaultMimeTypes)
  res.body = target.binread
end

trap("INT") { server.shutdown }
trap("TERM") { server.shutdown }

puts "Serving IMSI preview at http://127.0.0.1:#{PORT}/imsi/"
server.start
